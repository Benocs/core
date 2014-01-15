#
# CORE
#
# based on:
#
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE-BOEING file included in this distribution.
#
# author: Tom Goff <thomas.goff@boeing.com>
#
# Copyright (C) 2014 Robert Wuttke <robert@benocs.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA


'''
ipaddr.py: helper objects for dealing with IPv4/v6 addresses.
'''

import socket
import struct
import random

# this is from Python3.3. for now (since we're targeting Python3.2, we use the
# locally cached version of this (future) module
from core.misc import ipaddress

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
            raise ValueError("invalid af/addr")

        self.af = af
        self.addr = addr
        self.addr_newstyle = tmp

    def isIPv4(self):
        return self.af == AF_INET

    def isIPv6(self):
        return self.af == AF_INET6

    def __str__(self):
        return self.addr_newstyle.compressed

    def __eq__(self, other):
        try:
            return self.addr_newstyle == other.addr_newstyle
        except:
            return False

    def __add__(self, other):
        if self.addr_newstyle.version == 4:
            return ipaddress.IPv4Address(self.addr_newstyle + other.addr_newstyle)
        elif self.addr_newstyle.version == 6:
            return ipaddress.IPv6Address(self.addr_newstyle + other.addr_newstyle)

    def __sub__(self, other):
        try:
            tmp = -int(other)
        except:
            return NotImplemented
        return self.__add__(tmp)

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
        return int(self.addr_newstyle)

class IPPrefix(object):
    def __init__(self, af, prefixstr):
        "prefixstr format: address/prefixlen"
        print('generating prefix for str: %s' % prefixstr)

        tmp = prefixstr.split("/")
        if len(tmp) > 2:
            raise ValueError("invalid prefix: '%s'" % prefixstr)
        if len(tmp) == 2:
            self.prefixlen = int(tmp[1])
        else:
            self.prefixlen = self.addrlen

        self.af = af
        if self.af == AF_INET:
            self.addrlen = 32
            self.prefix = ipaddress.IPv4Network(prefixstr, strict = False)
        elif self.af == AF_INET6:
            self.prefix = ipaddress.IPv6Network(prefixstr, strict = False)
            self.addrlen = 128
        else:
            raise ValueError("invalid address family: '%s'" % self.af)

    def __str__(self):
        print("IPADDR: family: %s, prefix: %s, len: %s" % (str(self.af),
                str(self.prefix), str(self.prefixlen)))
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
        addr = 0
        for i in range(-1, -(self.addrlen >> 3) - 1, -1):
            addr = (self.prefix[i] | (tmp & 0xff)) + addr
            tmp >>= 8
            if not tmp:
                break

        num_bytes = 0
        if i == -1:
            num_bytes = 1
        else:
            num_bytes = len(self.prefix) - i

        print('new address (int): %s' % str(addr))
        addr = self.prefix[:i] + addr.to_bytes(num_bytes, byteorder = 'big')
        print('new address (bytes): %s' % str(addr))
        return IPAddr(self.af, addr)

    def minaddr(self):
        return self.prefix.network_address + 1

    def maxaddr(self):
        return self.prefix.broadcast_address - 1

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
    try:
        tmp = socket.inet_pton(af, addrstr)
        return True
    except:
        return False

def isIPv4Address(addrstr):
    return isIPAddress(AF_INET, addrstr)

def isIPv6Address(addrstr):
    return isIPAddress(AF_INET6, addrstr)
