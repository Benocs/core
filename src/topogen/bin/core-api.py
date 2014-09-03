#!/usr/bin/env python3

# core-api - a CORE api wrapper
#
# Copyright (c) 2014 Robert Wuttke <flash@jpod.cc>
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import optparse
import sys
import time

from core.api import coreapi
from core.connection import CoreConnection
from core.connection import msg_types
from core.connection import TLVHelper

once = True
got_answer = False

def msg_callback(msg):
    global got_answer
    got_answer = True
    print(msg, flush=True)

def connectSession(connection, sessionid):
    data = "session flags=add number %s" % str(sessionid)
    result, msg_cls, flags, tlv_data = \
            TLVHelper.parse_tlv_stringlist(data.split())
    msg = msg_cls.pack(flags, tlv_data)
    connection.socket.sendall(msg)

if __name__ == "__main__" or __name__ == "__builtin__":

    def usage(umsg=None, err=0):
        sys.stdout.write("\n")
        if umsg:
            sys.stdout.write(umsg + "\n")
        parser.print_help()
        sys.exit(err)

    usagestr = ("usage: %prog [-h|--help] [options]")
    parser = optparse.OptionParser(usage=usagestr)
    parser.set_defaults(port=coreapi.CORE_API_PORT,
                                            host="localhost",
                                            session=None,
                                            tlv_help=False,
                                            once=False)

    parser.add_option("-p", "--port", dest="port", type=int,
                                        help="port to connect to, default: %d" \
                                            % parser.defaults['port'])
    parser.add_option("-a", "--host", dest="host", type=str,
                                        help="Host to connect to, default: %s" \
                                            % parser.defaults['host'])
    parser.add_option("-s", "--session", dest="session", type=str,
                                        help=("Session to join, default: "
                                            "Create a new session"))
    parser.add_option("-H", "--tlv-help", dest="tlv_help", action="store_true",
                                        help=("List available Message Types "
                                            "and their resp. TLVs"))
    parser.add_option("-1", "--once", dest="once", action="store_true",
                                        help=("Wait for one reply, then exit."))

    # parse command line opt
    (opt, args) = parser.parse_args()

    if opt.tlv_help:
        print('List of available Message Types and their resp. TLVs requested')
        for msg_type in msg_types.keys():
            print('msg_type: %s' % msg_type)
            for tlv_type in dir(coreapi):
                if tlv_type.startswith('CORE_TLV_%s' % msg_types[msg_type][2]):
                    tlvshort = tlv_type.lower().split('_')[3]
                    print('  tlv: %s' % tlvshort)
        sys.exit(0)

    connection = CoreConnection()
    connection.set_server(opt.host, opt.port)
    try:
        # connect to server
        connection.connect()
    except Exception as exc:
        print("[ERROR] Could not connect to server: %s" % exc)
        sys.exit(2)

    if len(args) > 0:
        usage(err=1)

    for msg_type in connection.msg_handler.handled_msg_types:
        connection.msg_handler.set_msg_callback(msg_type, msg_callback)

    if not opt.session is None:
        connectSession(connection, str(opt.session))

    # serve forever (or until CTRL+C is pressed)
    while True:
        try:
            data = sys.stdin.readline().split()
            if len(data) == 0:
                if opt.once and got_answer:
                    time.sleep(0.1)
                    break
                time.sleep(0.1)
                continue
            result, msg_cls, flags, tlv_data = \
                    TLVHelper.parse_tlv_stringlist(data)
            if result:
                msg = msg_cls.pack(flags, tlv_data)
                #print('%s: sending data: %s' % (str(time.time()), str(msg)),
                #    file=sys.stderr)
                connection.socket.sendall(msg)
        except KeyboardInterrupt:
            print("CTRL+C pressed")
            sys.exit(0)

    sys.exit(0)
