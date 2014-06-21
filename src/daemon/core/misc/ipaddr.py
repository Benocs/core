#
# CORE
#
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE.BOEING file included in this distribution.
#
# author: Tom Goff <thomas.goff@boeing.com>
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

'''
ipaddr.py: helper objects for dealing with IPv4/v6 addresses.
'''

import socket
import struct
import random

import ipaddress

from core.constants import *
from core.misc.netid import NetIDNodeMap
from core.misc.netid import NetIDSubnetMap

AF_INET = socket.AF_INET
AF_INET6 = socket.AF_INET6

class MacAddr(object):
    def __init__(self, addr):
        self.addr = addr

    def __str__(self):
        return ":".join([("%02x" % x) for x in self.addr])

    def tolinklocal(self):
        ''' Convert the MAC address to a IPv6 link-local address, using EUI 48
        to EUI 64 conversion process per RFC 5342.
        '''
        if not self.addr:
            return IPAddr.fromstring("::")
        tmp = struct.unpack("!Q", '\x00\x00' + self.addr)[0]
        nic = int(tmp) & 0x000000FFFFFF
        oui = int(tmp) & 0xFFFFFF000000
        # toggle U/L bit
        oui ^= 0x020000000000
        # append EUI-48 octets
        oui = (oui << 16) | 0xFFFE000000
        return IPAddr(AF_INET6,  struct.pack("!QQ", 0xfe80 << 48, oui | nic))

    @classmethod
    def fromstring(cls, s):
        addr = "".join([chr(int(x, 16)) for x in s.split(":")])
        return cls(addr)

    @classmethod
    def random(cls):
        tmp = random.randint(0, 0xFFFFFF)
        tmp |= 0x00163E << 24    # use the Xen OID 00:16:3E
        tmpbytes = struct.pack("!Q", tmp)
        return cls(tmpbytes[2:])

class IPAddr(object):
    def __init__(self, af, addr):
        # check if (af, addr) is valid
        tmp = None
        try:
            if af == AF_INET:
                tmp = ipaddress.IPv4Address(addr)
            elif af == AF_INET6:
                tmp = ipaddress.IPv6Address(addr)
            else:
                raise ValueError("invalid af/addr")
        except:
            raise ValueError("invalid af/addr: \"%s\", \"%s\"" % (str(af),
                    str(addr)))

        self.af = af
        self.addr = tmp
        if af == AF_INET:
            # assume a /32 as default prefix length
            self.prefixlen = 32
        else:
            # assume a /128 as default prefix length
            self.prefixlen = 128

    def set_prefixlen(self, prefixlen):
        if not isinstance(prefixlen, int):
            raise ValueError('prefixlen needs to be a number')

        self.prefixlen = prefixlen

    def get_prefixlen(self):
        return self.prefixlen

    def isIPv4(self):
        return self.af == AF_INET

    def isIPv6(self):
        return self.af == AF_INET6

    def __repr__(self):
        return '%s/%d' % (self.addr.compressed, self.prefixlen)

    def __str__(self):
        return self.addr.compressed

    def __eq__(self, other):
        try:
            return self.addr == other.addr
        except:
            return False

    def __add__(self, other):
        if not self.__class__ == other.__class__ and not isinstance(other, int):
            raise ValueError
        if isinstance(other, IPAddr):
            if self.addr.version == 4:
                return IPAddr(AF_INET,
                        str(ipaddress.IPv4Address(self.addr + other.addr)))
            elif self.addr.version == 6:
                return IPAddr(AF_INET6,
                        str(ipaddress.IPv6Address(self.addr + other.addr)))
        elif isinstance(other, ipaddress.IPv4Address):
            return IPAddr(AF_INET, str(ipaddress.IPv4Address(self.addr + other)))
        elif isinstance(other, ipaddress.IPv6Address):
            return IPAddr(AF_INET6, str(ipaddress.IPv6Address(self.addr + other)))
        elif isinstance(other, int):
            return self.__class__(self.addr + other)
        else:
            return NotImplemented

    def __sub__(self, other):
        try:
            tmp = -int(other.addr)
        except:
            return NotImplemented
        return self.__add__(tmp)

    def __le__(self, other):
        return self.addr.__le__(other.addr)

    def __lt__(self, other):
        return self.addr.__lt__(other.addr)

    @classmethod
    def fromstring(cls, s):
        for af in AF_INET, AF_INET6:
            try:
                return cls(af, socket.inet_pton(af, s))
            except Exception as e:
                pass
        raise e

    @staticmethod
    def toint(s):
        ''' convert IPv4 string to 32-bit integer
        '''
        return int(self.addr)

class IPv4Addr(IPAddr):
    def __init__(self, addr):
        super().__init__(AF_INET, addr)

class IPv6Addr(IPAddr):
    def __init__(self, addr):
        super().__init__(AF_INET6, addr)

class IPPrefix(object):
    def __init__(self, af, prefixstr):
        "prefixstr format: address/prefixlen"

        self.af = af
        if self.af == AF_INET:
            self.addrlen = 32
            self.prefix = ipaddress.IPv4Network(prefixstr, strict = False)
        elif self.af == AF_INET6:
            self.prefix = ipaddress.IPv6Network(prefixstr, strict = False)
            self.addrlen = 128
        else:
            raise ValueError("invalid address family: '%s'" % self.af)

        tmp = prefixstr.split("/")
        if len(tmp) > 2:
            raise ValueError("invalid prefix: '%s'" % prefixstr)
        if len(tmp) == 2:
            self.prefixlen = int(tmp[1])
        else:
            self.prefixlen = self.addrlen

    def __str__(self):
        return str(self.prefix)

    def __eq__(self, other):
        try:
            return other.af == self.af and \
                other.prefixlen == self.prefixlen and \
                other.prefix == self.prefix
        except:
            return False

    def addr(self, hostid):
        tmp = int(hostid)
        if (tmp == 1 or tmp == 0 or tmp == -1) and self.addrlen == self.prefixlen:
            return IPAddr(self.af, self.prefix)
        if tmp == 0 or \
            tmp > (1 << (self.addrlen - self.prefixlen)) - 1 or \
            (self.af == AF_INET and tmp == (1 << (self.addrlen - self.prefixlen)) - 1):
            raise ValueError("invalid hostid for prefix %s: %s" % (str(self), str(hostid)))

        addr = IPAddr(self.af, int(self.prefix.network_address) + int(hostid))
        return addr

    def minaddr(self):
        if self.af == AF_INET:
            return IPv4Addr(self.prefix.network_address + 1)
        elif self.af == AF_INET6:
            return IPv6Addr(self.prefix.network_address + 1)
        else:
            raise ValueError("invalid address family: '%s'" % self.af)

    def maxaddr(self):
        if self.af == AF_INET:
            return IPv4Addr(self.prefix.broadcast_address - 1)
        elif self.af == AF_INET6:
            return IPv6Addr(self.prefix.broadcast_address - 1)
        else:
            raise ValueError("invalid address family: '%s'" % self.af)

    def numaddr(self):
        return self.prefix.num_addresses - 2

    def prefixstr(self):
        return '%s' % self.prefix

    def netmaskstr(self):
        return '%s' % self.prefix.netmask

class IPv4Prefix(IPPrefix):
    def __init__(self, prefixstr):
        IPPrefix.__init__(self, AF_INET, prefixstr)

class IPv6Prefix(IPPrefix):
    def __init__(self, prefixstr):
        IPPrefix.__init__(self, AF_INET6, prefixstr)

def isIPAddress(af, addrstr):
    if af == AF_INET and isinstance(addrstr, IPv4Addr):
        return True
    if af == AF_INET6 and isinstance(addrstr, IPv6Addr):
        return True
    if isinstance(addrstr, IPAddr):
        return True
    try:
        (ip, sep, mask) = addrstr.partition('/')
        tmp = socket.inet_pton(af, ip)
        return True
    except:
        return False

def isIPv4Address(addrstr):
    if isinstance(addrstr, IPv4Addr):
        return True
    if isinstance(addrstr, IPAddr):
        addrstr = str(addrstr)
    return isIPAddress(AF_INET, addrstr)

def isIPv6Address(addrstr):
    if isinstance(addrstr, IPv6Addr):
        return True
    if isinstance(addrstr, IPAddr):
        addrstr = str(addrstr)
    return isIPAddress(AF_INET6, addrstr)

class Interface():
    @staticmethod
    def cfg_sanitation_checks(ipversion):
        interface_net = 'ipv%d_interface_net' % ipversion
        interface_net_per_netid = 'ipv%d_interface_net_per_netid' % ipversion
        interface_net_per_ptp_link = 'ipv%d_interface_net_per_ptp_link' % \
                ipversion
        interface_net_per_brdcst_link = 'ipv%d_interface_net_per_brdcst_link' %\
                ipversion

        if not 'ipaddrs' in CONFIGS or \
                not interface_net in CONFIGS['ipaddrs'] or \
                not len(CONFIGS['ipaddrs'][interface_net].split('/')) == 2 or \
                not interface_net_per_netid in CONFIGS['ipaddrs'] or \
                not interface_net_per_ptp_link in CONFIGS['ipaddrs'] or \
                not interface_net_per_brdcst_link in CONFIGS['ipaddrs']:
            raise ValueError('Could not read ipaddrs.conf')

    @staticmethod
    def getInterfaceNet(ipversion):
        Interface.cfg_sanitation_checks(ipversion=ipversion)

        interface_net = 'ipv%d_interface_net' % ipversion
        interface_net_per_netid = 'ipv%d_interface_net_per_netid' % ipversion

        if ipversion == 4:
            ipprefix_cls = IPv4Prefix
        elif ipversion == 6:
            ipprefix_cls = IPv6Prefix
        else:
            raise ValueError('IP version is neither 4 nor 6: %s' % str(ipversion))

        global_interface_prefix_str = CONFIGS['ipaddrs'][interface_net]
        global_prefixbase, global_prefixlen = global_interface_prefix_str.split('/')
        try:
            global_prefixlen = int(global_prefixlen)
        except ValueError:
            raise ValueError('Could not parse %s from ipaddrs.conf' % interface_net)

        global_interface_prefix = ipprefix_cls(global_interface_prefix_str)
        return global_interface_prefix

    @staticmethod
    def getInterfaceNet_per_net(sessionid, netid, ipversion):
        Interface.cfg_sanitation_checks(ipversion=ipversion)

        interface_net = 'ipv%d_interface_net' % ipversion
        interface_net_per_netid = 'ipv%d_interface_net_per_netid' % ipversion

        if ipversion == 4:
            ipprefix_cls = IPv4Prefix
        elif ipversion == 6:
            ipprefix_cls = IPv6Prefix
        else:
            raise ValueError('IP version is neither 4 nor 6: %s' % str(ipversion))

        # local means per netid (e.g., AS)
        try:
            local_prefixlen = int(CONFIGS['ipaddrs'][interface_net_per_netid])
        except ValueError:
            raise ValueError('Could not parse %s from ipaddrs.conf' % interface_net_per_netid)

        global_interface_prefix = Interface.getInterfaceNet(ipversion)
        global_prefixbase, global_prefixlen = str(global_interface_prefix).split('/')

        subnet_id = NetIDSubnetMap.register_netid(sessionid, netid, ipversion)

        baseprefix = ipprefix_cls('%s/%d' % (global_prefixbase, local_prefixlen))
        target_network_baseaddr = baseprefix.minaddr() + ((subnet_id) * (baseprefix.numaddr() + 2))
        target_network_prefix = ipprefix_cls('%s/%d' % (target_network_baseaddr, local_prefixlen))
        return target_network_prefix

class Loopback():
    @staticmethod
    def cfg_sanitation_checks(ipversion):
        loopback_net = 'ipv%d_loopback_net' % ipversion
        loopback_net_per_netid = 'ipv%d_loopback_net_per_netid' % ipversion

        if not 'ipaddrs' in CONFIGS or \
                not loopback_net in CONFIGS['ipaddrs'] or \
                not len(CONFIGS['ipaddrs'][loopback_net].split('/')) == 2 or \
                not loopback_net_per_netid in CONFIGS['ipaddrs']:
            raise ValueError('Could not read ipaddrs.conf')

    @staticmethod
    def getLoopbackNet(ipversion):
        Loopback.cfg_sanitation_checks(ipversion=ipversion)

        loopback_net = 'ipv%d_loopback_net' % ipversion
        loopback_net_per_netid = 'ipv%d_loopback_net_per_netid' % ipversion

        if ipversion == 4:
            ipprefix_cls = IPv4Prefix
        elif ipversion == 6:
            ipprefix_cls = IPv6Prefix
        else:
            raise ValueError('IP version is neither 4 nor 6: %s' % str(ipversion))

        global_loopback_prefix_str = CONFIGS['ipaddrs'][loopback_net]
        global_prefixbase, global_prefixlen = global_loopback_prefix_str.split('/')
        try:
            global_prefixlen = int(global_prefixlen)
        except ValueError:
            raise ValueError('Could not parse %s from ipaddrs.conf' % loopback_net)

        global_loopback_prefix = ipprefix_cls(global_loopback_prefix_str)
        return global_loopback_prefix

    @staticmethod
    def getLoopbackNet_per_net(sessionid, netid, ipversion):
        Loopback.cfg_sanitation_checks(ipversion=ipversion)

        loopback_net = 'ipv%d_loopback_net' % ipversion
        loopback_net_per_netid = 'ipv%d_loopback_net_per_netid' % ipversion

        if ipversion == 4:
            ipprefix_cls = IPv4Prefix
        elif ipversion == 6:
            ipprefix_cls = IPv6Prefix
        else:
            raise ValueError('IP version is neither 4 nor 6: %s' % str(ipversion))

        # local means per netid (e.g., AS)
        try:
            local_prefixlen = int(CONFIGS['ipaddrs'][loopback_net_per_netid])
        except ValueError:
            raise ValueError('Could not parse %s from ipaddrs.conf' % loopback_net_per_netid)

        global_loopback_prefix = Loopback.getLoopbackNet(ipversion)
        global_prefixbase, global_prefixlen = str(global_loopback_prefix).split('/')

        subnet_id = NetIDSubnetMap.register_netid(sessionid, netid, ipversion)

        baseprefix = ipprefix_cls('%s/%d' % (global_prefixbase, local_prefixlen))
        target_network_baseaddr = baseprefix.minaddr() + ((subnet_id) * (baseprefix.numaddr() + 2))
        target_network_prefix = ipprefix_cls('%s/%d' % (target_network_baseaddr, local_prefixlen))
        return target_network_prefix

    @staticmethod
    def getLoopback(node, ipversion):
        Loopback.cfg_sanitation_checks(ipversion=ipversion)

        if hasattr(node, 'netid') and not node.netid is None:
            netid = node.netid
        else:
            # TODO: netid 0 is invalid - instead use first unused ASN
            node.warn('[LOOPBACK] no ASN found. falling back to default (0)')
            netid = 0

        target_network_prefix =  Loopback.getLoopbackNet_per_net(
                node.session.sessionid, netid, ipversion)

        nodeid = NetIDNodeMap.register_node(node.session.sessionid,
                node.nodeid(), netid)
        addr = target_network_prefix.addr(nodeid)
        #node.info('[LOOPBACK] generated addr for node: %s: %s' % (node.name, str(addr)))

        return addr

    @staticmethod
    def getLoopbackIPv4(node):
        return Loopback.getLoopback(node, ipversion=4)

    @staticmethod
    def getLoopbackIPv6(node):
        return Loopback.getLoopback(node, ipversion=6)
