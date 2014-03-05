#
# helper classes for clients to interact with CORE via its API
#
# Copyright (C) 2014 Benocs GmbH.
# See the LICENSE file included in this distribution.
#
# author: Robert Wuttke <robert@benocs.com>
#

import sys
import time

from core import pycore
from core.constants import *
from core.api import coreapi

def is_number(s):
    try:
        float(s)
        return True
    except ValueError:
        return False

msg_types = {
        'node': (1, coreapi.CORE_API_NODE_MSG, 'NODE'),
        'link': (2, coreapi.CORE_API_NODE_MSG, 'LINK'),
        'execute': (3, coreapi.CORE_API_EXEC_MSG, 'EXEC'),
        'register': (4, coreapi.CORE_API_REG_MSG, 'REG'),
        'configuration': (5, coreapi.CORE_API_CONF_MSG, 'CONF'),
        'file': (6, coreapi.CORE_API_FILE_MSG, 'FILE'),
        'interface': (7, coreapi.CORE_API_IFACE_MSG, 'IFACE'),
        'event': (8, coreapi.CORE_API_EVENT_MSG, 'EVENT'),
        'session': (9, coreapi.CORE_API_SESS_MSG, 'SESS'),
        'exception': (10, coreapi.CORE_API_EXCP_MSG, 'EXCP')
        }


class MsgHandler():

    master = None
    localport = None
    socket = None
    handled_msg_types = None

    def __init__(self):
        self.master = False
        self.localport = None
        self.socket = None

        self.setup()

    def setup(self):
        self.handled_msg_types = {
                    coreapi.CORE_API_SESS_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_CONF_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_EVENT_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_EXCP_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_EXEC_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_FILE_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_IFACE_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_LINK_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_NODE_MSG:
                            {'handler': None, 'callbacks': []},
                    coreapi.CORE_API_REG_MSG:
                            {'handler': None, 'callbacks': []},
                }

    def set_local_port(self, port):
        self.localport = port

    def set_socket(self, socket):
        self.socket = socket

    def set_msg_callback(self, msg_type, callback):
        if not msg_type in self.handled_msg_types:
            print('[ERROR] unsupported msg_type: %s' % str(msg_type))
            return False

        if callback in self.handled_msg_types[msg_type]:
            print('[ERROR] callback already registered')
            return False

        self.handled_msg_types[msg_type]['callbacks'].append(callback)
        return True

    def decode_message(self, data):
        ''' Retrieve a message from a socket and return the CoreMessage object or
                None upon disconnect. Socket data beyond the first message is dropped.
        '''
        msghdr = data[:coreapi.CoreMessage.hdrsiz]
        if len(msghdr) == 0:
            return None
        msgdata = None
        msgtype, msgflags, msglen = coreapi.CoreMessage.unpackhdr(msghdr)
        if msglen:
            msgdata = data[coreapi.CoreMessage.hdrsiz:]
        try:
            msgcls = coreapi.msg_class(msgtype)
        except KeyError:
            msg = coreapi.CoreMessage(msgflags, msghdr, msgdata)
            msg.msgtype = msgtype
            print("unimplemented CORE message type: %s" % msg.typestr())
            return msg
        if len(data) > msglen + coreapi.CoreMessage.hdrsiz:
            print("received a message of type %d, dropping %d bytes of extra data" \
                        % (msgtype, len(data) - (msglen + coreapi.CoreMessage.hdrsiz)))
        return msgcls(msgflags, msghdr, msgdata)

    def sendall(self, msg):
        # i really don't like the way CORE named its methods.
        # in my opinion, sendall should be named recv_msg() which is imho more readable
        self.recv_msg(msg)

    def recv_msg(self, msg):
        print('rawmsg(%d): %s' % (len(str(msg)), str(msg)), end='\n', file=sys.stderr, flush = True)
        msg = self.decode_message(msg)

        # TODO: move printing of incoming messages to it's own handler
        print(msg, end='\n', file=sys.stdout, flush = True)
        #print(msg, end='\n', file=sys.stderr, flush = True)
        sys.stdout.flush()
        sys.stderr.flush()
        spaces = []
        for i in range(10000):
            spaces.append(" ")
        print("".join(spaces), file=sys.stdout, flush = True)
        print("".join(spaces), file=sys.stdout, flush = True)
        sys.stdout.flush()

        """
        if msg.msgtype in self.handled_msg_types:
            if not self.handled_msg_types[msg.msgtype]['handler'] is None:
                self.handled_msg_types[msg.msgtype]['handler'](msg)
            for callback in self.handled_msg_types[msg.msgtype]['callbacks']:
                callback(msg)
        else:
            print('[ERROR] message type not supported: %d: %s' %
                    (msg.type, msg.typestr()))
        """

class CoreConnection():

    session = None
    server = None
    port = None
    localport = None
    socket = None
    msg_handler = None
    requested_session = None
    requested_session_connected = None

    def __init__(self, persistent = True):
        self.session = pycore.Session(persistent = persistent)
        self.session.verbose = True
        self.session.broker.verbose = True
        # TODO: mv to config-file
        self.session.cfg['clientlogfile'] = '/var/log/core-client.log'

        self.server = None
        self.port = None

        self.localport = None
        self.socket = None

        self.set_message_handler()
        #self.msg_handler.set_msg_callback(coreapi.CORE_API_SESS_MSG,
        #       self.__connect_to_session_callback__)

        self.requested_session = None
        self.requested_session_connected = False

        # declare classes for use with Broker
        coreapi.add_node_class("CORE_NODE_DEF",
                coreapi.CORE_NODE_DEF, pycore.nodes.CoreNode)
        coreapi.add_node_class("CORE_NODE_PHYS",
                                                     coreapi.CORE_NODE_PHYS, pycore.pnodes.PhysicalNode)
        try:
            coreapi.add_node_class("CORE_NODE_XEN",
                    coreapi.CORE_NODE_XEN, pycore.xen.XenNode)
        except Exception:
            pass
        coreapi.add_node_class("CORE_NODE_TBD",
                coreapi.CORE_NODE_TBD, None)
        coreapi.add_node_class("CORE_NODE_SWITCH",
                coreapi.CORE_NODE_SWITCH, pycore.nodes.SwitchNode)
        coreapi.add_node_class("CORE_NODE_HUB",
                coreapi.CORE_NODE_HUB, pycore.nodes.HubNode)
        coreapi.add_node_class("CORE_NODE_WLAN",
                coreapi.CORE_NODE_WLAN, pycore.nodes.WlanNode)
        coreapi.add_node_class("CORE_NODE_RJ45",
                coreapi.CORE_NODE_RJ45, pycore.nodes.RJ45Node)
        coreapi.add_node_class("CORE_NODE_TUNNEL",
                coreapi.CORE_NODE_TUNNEL, pycore.nodes.TunnelNode)
        coreapi.add_node_class("CORE_NODE_EMANE",
                coreapi.CORE_NODE_EMANE, pycore.nodes.EmaneNode)

    def set_server(self, server, port = None):
        self.server = server
        self.port = port

    def set_local_port(self, port):
        self.localport = port
        if not self.msg_handler is None:
            self.msg_handler.set_local_port(port)

    def set_socket(self, socket):
        self.socket = socket
        if not self.msg_handler is None:
            self.msg_handler.set_socket(socket)

    def connect(self):
        if self.server is None:
            return

        if self.port is None:
            port = coreapi.CORE_API_PORT
        else:
            port = self.port

        self.session.broker.addserver(self.server, self.server, port)

        if self.session.broker.servers[self.server][2] is None:
            self.session.broker.delserver(self.server)
            return False

        self.set_local_port(self.session.broker.servers[self.server][2].getsockname()[1])
        self.set_socket(self.session.broker.servers[self.server][2])

        return True

    def disconnect(self):
        self.session.broker.delserver(self.server)
        self.socket = None
        self.localport = None
        self.msg_handler.set_socket(None)
        self.msg_handler.set_localport(None)

    def set_message_handler(self, callback = None):
        if callback is None:
            self.msg_handler = MsgHandler()
        else:
            self.msg_handler = callback
        self.session.connect(self.msg_handler)
        return self.msg_handler

