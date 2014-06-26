#
# helper classes for clients to interact with CORE via its API
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
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
        msg = self.decode_message(msg)

        if msg.msgtype in self.handled_msg_types:
            if not self.handled_msg_types[msg.msgtype]['handler'] is None:
                self.handled_msg_types[msg.msgtype]['handler'](msg)
            for callback in self.handled_msg_types[msg.msgtype]['callbacks']:
                callback(msg)
        else:
            print('[ERROR] message type not supported: %d: %s' %
                    (msg.type, msg.typestr()))

class TLVHelper():

    @staticmethod
    def str_to_msgtypenum(s):
        """ Convert a shorthand string into a message type number """
        fulltypestr = str_to_msgtypename(s)
        for k, v in coreapi.message_types.items():
            if v == fulltypestr:
                return k
        return None

    @staticmethod
    def str_to_msgflagnum(s):
        flagname = "CORE_API_%s_FLAG" % s.upper()
        for (k, v) in coreapi.message_flags.items():
            if v == flagname:
                return k
        return None

    @staticmethod
    def tlvname_to_num(tlv_cls, name):
        """ Convert the given TLV Type class and TLV name to the TLV number  """
        for (k, v) in tlv_cls.tlvtypemap.items():
            if v == name:
                return k
        return None

    @staticmethod
    def str_to_tlvname(t, s):
        """ Convert the given TLV type t and string s to a TLV name """
        return "CORE_TLV_%s_%s" % (t.upper(), s.upper())

    @staticmethod
    def parse_tlv_stringlist(args):
        if len(args) < 3:
            print(('[ERROR] message too short. specify at least msgtype, tlvtype and '
                    'tlvdata'))
            return (False, None, 0, None)

        msg_type = args[0].lower()

        if not msg_type in msg_types:
            print('[ERROR] unsupported msg_type: %s' % msg_type)
            return (False, None, 0, None)

        if msg_types[msg_type][1] is None:
            print('[ERROR] msg_type: %s not implemented' % msg_type)
            return (False, None, 0, None)

        msg_cls = coreapi.msgclsmap[msg_types[msg_type][0]]
        tlv_cls = msg_cls.tlvcls

        # pop msg_type from arg list
        args.pop(0)

        flags_or_tlvtype = args[0].lower()
        flags = 0
        if flags_or_tlvtype.startswith('flags='):
            # build a message consisting of TLVs from 'type=value' arguments
            flagstr = flags_or_tlvtype.split('=')[1]
            for f in flagstr.split(","):
                if f == '':
                    continue
                n = TLVHelper.str_to_msgflagnum(f)
                if n is None:
                    print('[ERROR] Invalid flag "%s"' % f)
                    return (False, None, 0, None)
                flags |= n

            # pop flags from arg list
            args.pop(0)

        tlv_data_list = []
        while len(args) >= 2:
            tlv_type_raw = args.pop(0)
            tlv_value = args.pop(0)

            tlv_name = TLVHelper.str_to_tlvname(msg_types[msg_type][2], tlv_type_raw)
            tlv_type = TLVHelper.tlvname_to_num(tlv_cls, tlv_name)
            if tlv_name not in list(tlv_cls.tlvtypemap.values()):
                print("[ERROR] Unknown TLV: '%s' / %s:%s" % (tlv_type_raw, tlv_name, str(args)))
                return (False, None, 0, None)

            tlv_data_list.append(tlv_cls.packstring(tlv_type, tlv_value))

        tlv_data = b''.join(tlv_data_list)

        return (True, msg_cls, flags, tlv_data)

class CoreConnection():

    session = None
    server = None
    port = None
    localport = None
    socket = None
    msg_handler = None
    requested_session = None
    requested_session_connected = None

    def __init__(self, persistent = False):
        self.session = pycore.Session(persistent = persistent)
        self.session.verbose = False
        self.session.broker.verbose = False
        # TODO: mv to config-file
        self.session.cfg['clientlogfile'] = '/var/log/core-client.log'

        self.server = None
        self.port = None

        self.localport = None
        self.socket = None

        self.set_message_handler()

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
        self.msg_handler.set_local_port(None)

    def set_message_handler(self, callback = None):
        if callback is None:
            self.msg_handler = MsgHandler()
        else:
            self.msg_handler = callback
        self.session.connect(self.msg_handler)
        return self.msg_handler

