#
# CORE
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# author: Tom Goff <thomas.goff@boeing.com>
#
'''
ipaddr.py: helper objects for dealing with IPv4/v6 addresses.
'''

import socket
import struct
import random

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
        if not isinstance(addr, bytes):
            baddr = bytes(addr, encoding = 'utf-8')
        else:
            baddr = addr
        if not socket.inet_ntop(af, baddr):
            raise ValueError("invalid af/addr")
        self.af = af
        self.addr = addr

    def isIPv4(self):
        return self.af == AF_INET

    def isIPv6(self):
        return self.af == AF_INET6

    def __str__(self):
        return socket.inet_ntop(self.af, self.addr)

    def __eq__(self, other):
        try:
            return other.af == self.af and other.addr == self.addr
        except:
            return False

    def __add__(self, other):
        try:
            carry = int(other)
        except:
            return NotImplemented
        tmp = [ord(x) for x in self.addr]
        for i in range(len(tmp) - 1, -1, -1):
            x = tmp[i] + carry
            tmp[i] = x & 0xff
            carry = x >> 8
            if carry == 0:
                break
        addr = "".join([chr(x) for x in tmp])
        return self.__class__(self.af, addr)

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
        bin = socket.inet_pton(AF_INET, s)
        return(struct.unpack('!I', bin)[0])

class IPPrefix(object):
    def __init__(self, af, prefixstr):
        "prefixstr format: address/prefixlen"
        tmp = prefixstr.split("/")
        if len(tmp) > 2:
            raise ValueError("invalid prefix: '%s'" % prefixstr)
        self.af = af
        if self.af == AF_INET:
            self.addrlen = 32
        elif self.af == AF_INET6:
            self.addrlen = 128
        else:
            raise ValueError("invalid address family: '%s'" % self.af)
        if len(tmp) == 2:
            self.prefixlen = int(tmp[1])
        else:
            self.prefixlen = self.addrlen
        print('socket.inet_pton(%s, %s): %s' % (str(self.af), str(tmp[0]),
            str(socket.inet_pton(self.af, tmp[0]))))
        self.prefix = socket.inet_pton(self.af, tmp[0])
        if self.addrlen > self.prefixlen:
            addrbits = self.addrlen - self.prefixlen
            netmask = ((1 << self.prefixlen) - 1) << addrbits
            prefix = 0
            for i in range(-1, -(addrbits >> 3) - 2, -1):
                #print('self.prefix(%s) = self.prefix[:i](%s) + prefix(%s)' %
                #        (str(self.prefix), str(self.prefix[:i]), str(prefix)))
                prefix = (self.prefix[i] & (netmask & 0xff)) + prefix
                netmask >>= 8
            #print('i: %d, len(self.prefix): %d' % (i, len(self.prefix)))
            num_bytes = 0
            if i == -1:
              num_bytes = 1
            else:
              num_bytes = len(self.prefix) - i
            self.prefix = self.prefix[:i] + prefix.to_bytes(num_bytes, byteorder = 'big')
            print('new prefix: %s' % str(self.prefix))

    def __str__(self):
        return "%s/%s" % (socket.inet_ntop(self.af, self.prefix),
                          str(self.prefixlen))

    def __eq__(self, other):
        try:
            return other.af == self.af and \
                other.prefixlen == self.prefixlen and \
                other.prefix == self.prefix
        except:
            return False

    def __add__(self, other):
        try:
            tmp = int(other)
        except:
            return NotImplemented
        a = IPAddr(self.af, self.prefix) + \
            (tmp << (self.addrlen - self.prefixlen))
        prefixstr = "%s/%s" % (a, self.prefixlen)
        if self.__class__ == IPPrefix:
            return self.__class__(self.af, prefixstr)
        else:
            return self.__class__(prefixstr)

    def __sub__(self, other):
        try:
            tmp = -int(other)
        except:
            return NotImplemented
        return self.__add__(tmp)

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

        addr = self.prefix[:i] + addr.to_bytes(num_bytes, byteorder = 'big')
        print('new address: %s' % str(addr))
        return IPAddr(self.af, addr)

    def minaddr(self):
        return self.addr(1)

    def maxaddr(self):
        if self.af == AF_INET:
            return self.addr((1 << (self.addrlen - self.prefixlen)) - 2)
        else:
            return self.addr((1 << (self.addrlen - self.prefixlen)) - 1)

    def numaddr(self):
        return max(0, (1 << (self.addrlen - self.prefixlen)) - 2)
        
    def prefixstr(self):
        return "%s" % socket.inet_ntop(self.af, self.prefix)
    
    def netmaskstr(self):
        addrbits = self.addrlen - self.prefixlen
        netmask = ((1 << self.prefixlen) - 1) << addrbits
        netmaskbytes = struct.pack("!L",  netmask)
        return IPAddr(af=AF_INET, addr=netmaskbytes).__str__()

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
