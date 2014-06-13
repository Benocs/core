# various CORE services that implement dns-services
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

# TODO fix pid names
import os

from socket import AF_INET
from socket import AF_INET6

from core.service import CoreService, addservice
from core.misc.ipaddr import IPv4Addr, IPv6Addr
from core.misc.ipaddr import IPv4Prefix, IPv6Prefix
from core.misc.ipaddr import isIPv4Address, isIPv6Address
from core.misc.ipaddr import Loopback, Interface
from core.misc.ipaddr import NetIDNodeMap
from core.misc.utils import *
from core.constants import *

from core.services import service_helpers
from core.services import service_flags

class DNSServices(CoreService):
    """ Parent class for DNS services """
    _name = "DNS services"
    _group = "DNS"
    _depends = ()
    _dirs = ()
    _configs = ()
    _startindex = 80
    _startup = ()
    _shutdown = ()

    @classmethod
    def generateconfig(cls,  node, filename, services):
        return ""

class Bind9(DNSServices):
    """ Bind9 service for nodes """
    _name = "Bind9"
    _configs = ("/etc/bind/named.conf", "/etc/bind/named.conf.default-zones",
            "/etc/bind/named.conf.local", "/etc/bind/named.conf.options",
            "/etc/default/bind")
    _dirs = (("/etc/bind", "union"), ("/var/cache/bind", "bind"),
            ("/var/log", "bind"), ("/etc/default", "union"))
    _startindex = 99
    _startup = ("service bind9 start",)
    _shutdown = ("service bind9 stop",)
    #_validate = ("service bind9 status",)
    _meta = "dns resolver service using Bind9"
    _starttime = 1

    @classmethod
    def generateconfig(cls, node, filename, services):
        """ Generate a Bind9 config """

        if filename == cls._configs[0]:
            return cls.generateNamedConf(cls, node, services)
        if filename == cls._configs[1]:
            return cls.generateDefaultZonesConf(cls, node, services)
        if filename == cls._configs[2]:
            return cls.generateNamedLocalConf(cls, node, services)
        if filename == cls._configs[3]:
            return cls.generateNamedOptionsConf(cls, node, services)
        if filename == cls._configs[4]:
            return cls.generateDefaultNamed(cls, node, services)

    @staticmethod
    def generateDefaultNamed(cls, node, services):
        return 'RESOLVCONF=no\nOPTIONS="-u bind -n1"\n'

    @staticmethod
    def generateNamedConf(cls, node, services):
        return ('include "%s";\ninclude "%s";\ninclude "%s";\n' %
                (cls._configs[1], cls._configs[2], cls._configs[3]))

    @staticmethod
    def generateDefaultZonesConf(cls, node, services):
        cfgitems = cls.generateDefaultDefaultZonesConf(cls)
        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateNamedLocalConf(cls, node, services):
        cfgitems = cls.generateDefaultLocalConf(cls)
        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateNamedOptionsConf(cls, node, services):
        cfgitems = cls.generateDefaultOptionsConf(cls)
        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateDefaultDefaultZonesConf(cls, cfgitems = None):
        """ Generate default Bind9 default zones config """

        if cfgitems is None:
            cfgitems = {}

        # prime the server with knowledge of the root servers
        cls.cfg_add_item(cfgitems, 'zone "."', 'type hint;')
        cls.cfg_add_item(cfgitems, 'zone "."', 'file "/etc/bind/db.root";')

        # be authoritative for the localhost forward and reverse zones, and for
        # broadcast zones as per RFC 1912
        cls.cfg_add_item(cfgitems, 'zone "localhost"', 'type master;')
        cls.cfg_add_item(cfgitems, 'zone "localhost"',
                'file "/etc/bind/db.local";')

        cls.cfg_add_item(cfgitems, 'zone "127.in-addr.arpa"', 'type master;')
        cls.cfg_add_item(cfgitems, 'zone "127.in-addr.arpa"',
                'file "/etc/bind/db.127";')

        cls.cfg_add_item(cfgitems, 'zone "0.in-addr.arpa"', 'type master;')
        cls.cfg_add_item(cfgitems, 'zone "0.in-addr.arpa"',
                'file "/etc/bind/db.0";')

        cls.cfg_add_item(cfgitems, 'zone "255.in-addr.arpa"', 'type master;')
        cls.cfg_add_item(cfgitems, 'zone "255.in-addr.arpa"',
                'file "/etc/bind/db.255";')

        return cfgitems

    @staticmethod
    def generateSOAHeader(cls, auth_nameservers, zone,
            serial = 2014010123,
            ttl = 900, refresh = 900, retry = 450,
            expire = 3600000, negcache = 900):
        """ auth_nameservers is expected to be a list of
            tuples with each tuple being made up of:
                * a fqdn-string (including the trailing dot)
                * the main IP address of the nameserver

        """

        print(('[DEBUG] generating SOA header for zone: %s, served by: %s' % (str(zone),
                str(auth_nameservers))))

        if not isinstance(auth_nameservers, list) or \
                len(auth_nameservers) == 0 or \
                not isinstance(auth_nameservers[0], tuple) or \
                not len(auth_nameservers[0]) == 2 or \
                not isinstance(zone, str) or \
                not isinstance(serial, int) or \
                not isinstance(ttl, int) or \
                not isinstance(refresh, int) or \
                not isinstance(retry, int) or \
                not isinstance(expire, int) or \
                not isinstance(negcache, int):
            raise ValueError

        # create  list of name server-names (drop their addresses)
        nameservers = list([x[0] for x in auth_nameservers])

        soaitems = []
        soaitems.append('$TTL %d\n' % ttl)
        soaitems.append('; (serial refresh retry expire negative_cache)\n')

        soaitems.append('@ IN SOA %s root.%s' % (nameservers[0], nameservers[0]))
        soaitems.append(' (%d %d %d %d %d)\n' % (serial, refresh, retry, expire, negcache))

        soaitems.append('%s\n' % '\n'.join(set(['  IN NS %s' % x[0] for x in auth_nameservers])))

        return ''.join(soaitems)

    @staticmethod
    def generateDelegationRecord(cls, delegation_servers, zone):
        delegationitems = []
        delegationitems.append('$ORIGIN %s\n' % zone)
        tmp_servers = [server for server, server_addr in delegation_servers]
        # add each server once but only once (that's why the set is there)
        for server in set(tmp_servers):
            delegationitems.append('@ IN NS %s\n' % (server))

        for server, server_addr in delegation_servers:
            recordtype = ''
            if isIPv4Address(server_addr):
                recordtype = 'A'
            elif isIPv6Address(server_addr):
                recordtype = 'AAAA'
            else:
                raise ValueError
            delegationitems.append('%s %s %s\n' % (server, recordtype, server_addr))

        return ''.join(delegationitems)

    @staticmethod
    def getServers(cls, node, zone, nodewalker_cb):
        # add any authoritative dns server to the list of resolvers for that AS,
        # if we are not an authoritative dns server for the same AS
        servers = []
        service_helpers.nodewalker(node, node, servers, nodewalker_cb)

        # servers managing virtual zone
        zone_servers = []
        for servername, ipaddr, server_zone in servers:
            #print(('[DEBUG] candidate: server: %s, zone: %s' % (servername, server_zone)))
            if server_zone == zone:
                #print(('[DEBUG] adding to zone: "%s" server: "%s" (%s)' %
                #        (server_zone, servername, ipaddr)))
                zone_servers.append((servername, ipaddr))
        return servers, zone_servers

    @staticmethod
    def writeZoneFile(cls, node, zone, zonecontents):
        #print(("zone: %s: %s" % (zone, zonecontent)))
        ## TODO: handle the case when two tuples exit with both the same zone
        # rename root-zone from '.' to 'root'
        if zone == '.':
            zone = 'root'
        # strip '.' at end
        zone = zone.rstrip('.')
        # and write result
        node.nodefile('/etc/bind/db.%s' % zone, zonecontents)

    @staticmethod
    def generateDBAuthoritativeFile(cls, node, zone, nameservers_cb,
            delegation_servers_cb=None, hosts_cb=None):
        servers, zone_servers = cls.getServers(cls, node, zone, nameservers_cb)
        tmpservers = []
        for server, addr, server_zone in servers:
            if server_zone == '.':
                tmpservers.append(('%s.' % server, addr, server_zone))
            else:
                tmpservers.append(('%s.%s' % (server, server_zone), addr, server_zone))
        servers = tmpservers
        if zone == '.':
            zone_servers = [('%s.' % server, addr) for server, addr in zone_servers]
        else:
            zone_servers = [('%s.%s' % (server, zone), addr) for server, addr in zone_servers]
        #print(('[==DEBUG==] servers: %s' % servers))
        #print(('[==DEBUG==] zone_servers: %s' % zone_servers))

        rawzonecontents = cls.compileZoneFile(cls, list([(x[0], x[1], zone) for x in zone_servers]))[0]
        #print(('[DEBUG] generateDBAuthoritativeFile(node="%s", zone="%s"): zone_servers: %s' %
        #        (node, zone, zone_servers)))
        SOAHeader = cls.generateSOAHeader(cls, zone_servers, zone)
        #print(('[DEBUG] SOAHeader: %s' % SOAHeader))
        zonecontents = '%s\n%s' % (SOAHeader, rawzonecontents)
        #print(('[DEBUG] zonecontents: %s' % zonecontents))

        if not delegation_servers_cb is None:
            delegation_servers = []
            service_helpers.nodewalker(node, node, delegation_servers,
                    delegation_servers_cb)
            delegation_servers_map = {}
            for server, addr, server_zone in delegation_servers:
                if server_zone == '.':
                    servername = ('%s.' % server)
                else:
                    servername = ('%s.%s' % (server, server_zone))
                if not server_zone in delegation_servers_map:
                    delegation_servers_map[server_zone] = []
                delegation_servers_map[server_zone].append((servername, addr))
            delegation_records = []
            for server_zone, servers in delegation_servers_map.items():
                delegation_records.append(cls.generateDelegationRecord(cls, servers, server_zone))

            zonecontents = '%s\n%s' % (zonecontents, '\n\n'.join(delegation_records))

        if not hosts_cb is None:
            hosts = []
            service_helpers.nodewalker(node, node, hosts,
                     hosts_cb)
            # remove nameservers as they have already been added
            # TODO: remove nameservers as they have already been added -- hosts = [(server_name, v6addr, zone) for server_name, v6addr, zone ]
            host_records = cls.compileZoneFile(cls, None, hosts)[1]
            #print(('[DDEBUGG] host_records: %s' % str(host_records)))
            zonecontents = '%s\n%s' % (zonecontents, host_records)

        if len(servers) > 0:
            cls.writeZoneFile(cls, node, zone, zonecontents)

    @staticmethod
    def generateDBClientFile(cls, node, zone, nodewalker_cb):
        servers, zone_servers = cls.getServers(cls, node, zone, nodewalker_cb)
        zonecontents = cls.compileZoneFile(cls, list([(x[0], x[1], zone) for x in zone_servers]))[0]
        if len(servers) > 0:
            cls.writeZoneFile(cls, node, zone, zonecontents)

    @staticmethod
    def generateZoneContent(cls, node, zone, nodewalker_cb):
        servers, zone_servers = cls.getServers(cls, node, zone, nodewalker_cb)
        zonecontents = cls.compileZoneFile(cls, [], list([(x[0], x[1], zone) for x in zone_servers]))[1]
        if len(servers) > 0:
            cls.writeZoneFile(cls, node, zone, zonecontents)

    @staticmethod
    def getPTRZoneNameFromPrefix(cls, prefix):
        """ returns the reverse zone name of the given prefix """
        # IPv4
        if prefix.af == AF_INET:
            num_network_bytes = int(prefix.prefixlen / 8)
            net_list = str(prefix.minaddr()).split('.')[:num_network_bytes]
            net_list.reverse()
            zone_name = '%s.in-addr.arpa.' % '.'.join(net_list)
        # IPv6
        elif prefix.af == AF_INET6:
            # example prefixes
            # a: fd10::/16
            # b: fd10:1::/32

            # evaluates to:
            # a: 4
            # b: 8
            num_network_nibbles = int(prefix.prefixlen / 4)

            # net_str evaluates to:
            # a: fd10
            # b: fd100001
            prefix_str = prefix.prefix.network_address.exploded.replace(':', '')
            net_str = prefix_str[:num_network_nibbles]

            # net_list will be:
            # a: ['0', '1', 'd', 'f']
            # b: ['1', '0', '0', '0', '0', '1', 'd', 'f']
            net_list = []
            for c in net_str:
                net_list.append(c)
            net_list.reverse()

            # zone_name will be:
            # a: 0.1.d.f.ip6.arpa.
            # b: 1.0.0.0.0.1.d.f.ip6.arpa.
            zone_name = '%s.ip6.arpa.' % '.'.join(net_list)
        else:
            raise ValueError("invalid address family: '%s'" % prefix.af)
        return zone_name

    @staticmethod
    def getPTRSubnetFromPrefix_IPv4(cls, supernet_prefix, subnet_prefix):
        """ returns all reverse subnet names of the given prefix """
        # IPv4
        if subnet_prefix.af == AF_INET:
            num_network_bytes = int(supernet_prefix.prefixlen / 8)
            num_host_bytes = 4 - num_network_bytes
            host_list = str(subnet_prefix.prefix.network_address).split('.')[num_network_bytes:]
            return '%s/%s' % ('.'.join(host_list), subnet_prefix.prefixlen)
        else:
            raise ValueError('Only IPv4 is supported')

    @staticmethod
    def getPTR_CNAME_FromAddr(cls, addr):
        """ returns a CNAME record from this address """
        # IPv4
        if addr.isIPv4():
            num_network_bytes = int(addr.prefixlen / 8)
            addr_list = str(addr).split('.')[num_network_bytes:]
            addr_list.reverse()
            #print('[---==== DEBUG ====---] returning (%s) %s addr_list: %s' % \
            #        (str(addr), str(num_network_bytes), str(addr_list)))
            return '.'.join(addr_list)
        elif addr.isIPv6():
            num_network_nibbles = int(addr.prefixlen / 4)
            addr_str = addr.addr.exploded.replace(':', '')
            host_str = addr_str[num_network_nibbles:]
            host_list = []
            for c in host_str:
                host_list.append(c)
            host_list.reverse()
            return '.'.join(host_list)
        else:
            raise ValueError('Only IPv4 and IPv6 are supported')

    @staticmethod
    def getAndGeneratePTRZonesRootServer(cls, node):
        """ returns a list of all reverse zones a root dns server serves """

        # find dns root servers
        # (server_name, server_addr)
        rootservers = []
        service_helpers.nodewalker(node, node, rootservers,
                cls.nodewalker_find_root_dns_callback)
        rootservers = [('%s.' % server_name, server_addr) \
                for server_name, server_addr in rootservers]
        # find dns as authoritative servers
        # (server_name, server_addr, zone)
        as_auth_servers = []
        service_helpers.nodewalker(node, node, as_auth_servers,
                cls.nodewalker_root_dns_find_all_auth_servers_callback)
        as_auth_servers = [('%s.%s' % (server_name, zone), server_addr, zone) \
                for server_name, server_addr, zone in as_auth_servers]

        zonenames = []

        SOAHeader = cls.generateSOAHeader(cls, rootservers, '.')
        print(('[DEBUG] SOAHeader:\n%s' % SOAHeader))

        for ipversion in node.getIPversions():
            # collect loopback address space
            loopback_net = Loopback.getLoopbackNet(ipversion)
            print(('[DEBUG] loopback_net IPv%d: %s' % (ipversion, loopback_net)))

            # collect interface address space
            interface_net = Interface.getInterfaceNet(ipversion)
            print(('[DEBUG] interface_net IPv%d: %s' % (ipversion, interface_net)))

            # get all deployed ASN's
            asns = list(NetIDNodeMap.mapping.keys())
            print(('[DEBUG] deployed ASN\'s: %s' % asns))
            for net in loopback_net, interface_net:
                zonename = cls.getPTRZoneNameFromPrefix(cls, net)
                net_prefixlen = net.prefixlen
                print(('[DEBUG] zonename: %s' % zonename))

                ORIGINHeader = '$ORIGIN %s\n' % zonename
                print(('[DEBUG] ORIGINHeader: %s' % ORIGINHeader))

                zoneentries = []
                for asn in asns:
                    # get AS address space
                    if net == loopback_net:
                        asn_net = Loopback.getLoopbackNet_per_net(asn, ipversion)
                    elif net == interface_net:
                        asn_net = Interface.getInterfaceNet_per_net(asn, ipversion)

                    # find authoritative AS dns servers
                    # zone == "AS%s.virtual." % str(netid)
                    for server_name, server_addr, zone in as_auth_servers:
                        server_asn = zone.lstrip('AS')
                        server_asn = int(server_asn[:server_asn.find('.')])

                        # not the correct asn
                        if not asn == server_asn:
                            continue

                        # not our IP version
                        if ipversion == 4 and not isIPv4Address(server_addr):
                            continue
                        if ipversion == 6 and not isIPv6Address(server_addr):
                            continue

                        print(('[DEBUG] server_name: %s, server_addr: %s, zone: %s' %
                                (server_name, server_addr, zone)))

                        if ipversion == 4:
                            # get host list of this AS
                            # TODO: iterating over all nodes for each AS for interface and
                            # loopback address space is expensive. and we are only talking
                            # about IPv4 at the moment. is there a better way of doing this?
                            hosts = []
                            # TODO: tmp. setting another netid of a node is a dirty hack
                            tmpnetid = node.netid
                            node.netid = server_asn
                            service_helpers.nodewalker(node, node, hosts,
                                    cls.nodewalker_asroot_dns_find_hosts_in_as_callback)
                            node.netid = tmpnetid
                            for hostname, asn_addr, zone in hosts:
                                if not isIPv4Address(asn_addr):
                                    continue

                                asn_addr = IPv4Addr(asn_addr)

                                print(('[DEBUG] asn_addr(%s) in asn_net(%s)' %
                                        (str(asn_addr), str(asn_net))))

                                if asn_addr < asn_net.minaddr() or \
                                        asn_addr > asn_net.maxaddr():
                                    continue

                                # set prefix length of the supernet
                                asn_addr.set_prefixlen(net_prefixlen)
                                asn_ptr_name = cls.getPTR_CNAME_FromAddr(cls, asn_addr)

                                #print(('[DEBUG] deployed ASN network (IPv%d): %s' %
                                #        (ipversion, str(asn_net))))
                                print(('[DEBUG] ASN PTR addr (IPv%d): %s' %
                                        (ipversion, str(asn_addr))))

                                print(('[DEBUG] adding: "%s IN NS %s"' %
                                        (asn_ptr_name, server_name)))
                                zoneentries.append(('%s IN NS %s' %
                                        (asn_ptr_name, server_name)))
                        elif ipversion == 6:
                            asn_ptr_name = cls.getPTRZoneNameFromPrefix(cls, asn_net)
                            print(('[DEBUG] adding: "%s IN NS %s"' %
                                    (asn_ptr_name, server_name)))
                            zoneentries.append(('%s IN NS %s' %
                                    (asn_ptr_name, server_name)))

                print(('[DEBUG] subnet name servers: %s' % (zoneentries)))

                zonecontents = '%s\n%s\n%s\n' % (ORIGINHeader, SOAHeader,
                        '\n'.join(zoneentries))
                cls.writeZoneFile(cls, node, zonename, zonecontents)
                print(('[DEBUG] adding ptrzone to zonenames: %s' % zonename))
                zonenames.append(zonename)

        return zonenames

    @staticmethod
    def getAndGeneratePTRZonesASAuthServer(cls, node):
        """ returns a list of all reverse zones a root dns server serves """
        # find dns as authoritative servers
        # (server_name, server_addr, zone)
        as_auth_servers = []
        service_helpers.nodewalker(node, node, as_auth_servers,
                cls.nodewalker_root_dns_find_all_auth_servers_callback)
        as_auth_servers = [('%s.%s' % (server_name, zone), server_addr, zone) \
                for server_name, server_addr, zone in as_auth_servers]
        # zone = "AS%s.virtual." % str(netid)

        zonenames = []

        if hasattr(node, 'netid') and not node.netid is None:
            netid = node.netid
        else:
            # TODO: netid 0 is invalid
            netid = 0
        asn = netid

        for ipversion in node.getIPversions():
            # collect loopback address space
            loopback_net = Loopback.getLoopbackNet_per_net(netid, ipversion)
            print(('[DEBUG] loopback_net IPv%d: %s' % (ipversion, loopback_net)))

            # collect interface address space
            interface_net = Interface.getInterfaceNet_per_net(netid, ipversion)
            print(('[DEBUG] interface_net IPv%d: %s' % (ipversion, interface_net)))

            if ipversion == 4:
                auth_servers = [(server_name, server_addr) \
                        for server_name, server_addr, zone in as_auth_servers \
                        if zone == "AS%s.virtual." % str(netid) and \
                        isIPv4Address(server_addr)]
            elif ipversion == 6:
                auth_servers = [(server_name, server_addr) \
                        for server_name, server_addr, zone in as_auth_servers \
                        if zone == "AS%s.virtual." % str(netid) and \
                        isIPv6Address(server_addr)]
            else:
                raise ValueError

            for asn_net in loopback_net, interface_net:
                zonename = cls.getPTRZoneNameFromPrefix(cls, asn_net)
                print(('[DEBUG] zonename: %s' % zonename))

                ORIGINHeader = '$ORIGIN %s\n' % zonename
                print(('[DEBUG] ORIGINHeader: %s' % ORIGINHeader))

                SOAHeader = cls.generateSOAHeader(cls, auth_servers, zonename)
                print(('[DEBUG] SOAHeader:\n%s' % SOAHeader))

                zoneentries = []

                # get host list of this AS
                # TODO: iterating over all nodes for interface and
                # loopback address space is expensive. and we are only talking
                # about IPv4 or IPv6 at the moment.
                # is there a better way of doing this?
                hosts = []
                service_helpers.nodewalker(node, node, hosts,
                        cls.nodewalker_asroot_dns_find_hosts_in_as_callback)
                for hostname, asn_addr, zone in hosts:
                    if ipversion == 4 and not isIPv4Address(asn_addr):
                        continue
                    if ipversion == 6 and not isIPv6Address(asn_addr):
                        continue

                    if ipversion == 4:
                        asn_addr = IPv4Addr(asn_addr)
                    elif ipversion == 6:
                        asn_addr = IPv6Addr(asn_addr)
                    else:
                        raise ValueError

                    if asn_addr < asn_net.minaddr() or \
                            asn_addr > asn_net.maxaddr():
                        continue

                    # set prefix length. just to be sure
                    asn_addr.set_prefixlen(asn_net.prefixlen)
                    asn_ptr_name = cls.getPTR_CNAME_FromAddr(cls, asn_addr)

                    print(('[DEBUG] ASN PTR addr (IPv%d): %s' %
                            (ipversion, str(asn_addr))))

                    print(('[DEBUG] adding: "%s IN PTR %s.AS%s.virtual.' %
                            (asn_ptr_name, hostname, str(netid))))
                    zoneentries.append(('%s IN PTR %s.AS%s.virtual.' %
                            (asn_ptr_name, hostname, str(netid))))

                print(('[DEBUG] PTR records: %s' % (zoneentries)))

                zonecontents = '%s\n%s\n%s\n' % (ORIGINHeader, SOAHeader,
                        '\n'.join(zoneentries))
                cls.writeZoneFile(cls, node, zonename, zonecontents)
                print(('[DEBUG] adding ptrzone: %s' % zonename))
                zonenames.append(zonename)

        return zonenames

    @staticmethod
    def getAndGeneratePTRZones(cls, node):
        """ returns a list of all reverse zonenames a dns server serves """

        zonenames = []
        if service_flags.DNSRootServer in node.services:
            zonenames = cls.getAndGeneratePTRZonesRootServer(cls, node)
        elif service_flags.DNSASRootServer in node.services:
            zonenames = cls.getAndGeneratePTRZonesASAuthServer(cls, node)

        return zonenames

    @staticmethod
    def generateDefaultLocalConf(cls, cfgitems = None):
        """ Generate default Bind9 local config """

        if cfgitems is None:
            cfgitems = {}

        return cfgitems

    @staticmethod
    def generateDefaultOptionsConf(cls, cfgitems = None):
        """ Generate default Bind9 options """

        if cfgitems is None:
            cfgitems = {}

        cls.cfg_add_item(cfgitems, 'options',
                [
                'max-cache-ttl 10;',
                'max-ncache-ttl 10;',
                'max-cache-size 128M;',
                'directory "/var/cache/bind";',
                'dnssec-enable no;',
                'dnssec-validation no;',
                'auth-nxdomain no;    # conform to RFC1035'
                ])

        cls.cfg_add_item(cfgitems, ['options', 'listen-on port 53'], 'any;')
        cls.cfg_add_item(cfgitems, ['options', 'listen-on-v6'], 'any;')
        cls.cfg_add_item(cfgitems, ['options', 'allow-query'], 'any;')

        cls.cfg_add_item(cfgitems, 'logging')
        cls.cfg_add_item(cfgitems, ['logging', 'channel default_file'],
                'file "/var/log/named.log" size 10m;')
        cls.cfg_add_item(cfgitems, ['logging', 'channel default_file'],
                '//                      stderr;')
        cls.cfg_add_item(cfgitems, ['logging', 'channel default_file'],
                'severity info;')
        cls.cfg_add_item(cfgitems, ['logging', 'channel default_file'],
                'print-time yes;')
        cls.cfg_add_item(cfgitems, ['logging', 'channel default_file'],
                'print-severity yes;')
        cls.cfg_add_item(cfgitems, ['logging', 'channel default_file'],
                'print-category yes;')
        cls.cfg_add_item(cfgitems, ['logging', 'category default'],
                'default_file;')
        cls.cfg_add_item(cfgitems, ['logging', 'category queries'],
                'default_file;')
        cls.cfg_add_item(cfgitems, ['logging', 'category resolver'],
                'default_file;')

        return cfgitems

    @staticmethod
    def compile_named_conf(cls, named_cfg, cfgitems = None, level = 0):
        CFG_SECTION_VALUES = '__section_values__'
        if cfgitems is None:
            cfgitems = []
        for key, valueitems in list(named_cfg.items()):
            prefix_whitespace = ''.join(list([' ' for x in range(level*2)]))
            prefix_whitespace = '  %s' % prefix_whitespace
            if not key == CFG_SECTION_VALUES:
                cfgitems.append("%s%s {\n" % (prefix_whitespace, key))
            if isinstance(valueitems, dict):
                cls.compile_named_conf(cls, valueitems, cfgitems, level+1)
            elif isinstance(valueitems, list):
                cfgitems.extend(list([''.join([prefix_whitespace, x, '\n']) for x in valueitems]))
            elif isinstance(str(valueitems), str):
                cfgitems.append(''.join([prefix_whitespace,
                        str(valueitems), '\n']))
            else:
                raise ValueError
            if not key == CFG_SECTION_VALUES:
                cfgitems.append("%s};\n" % prefix_whitespace)
        return ''.join(cfgitems)

    @staticmethod
    def cfg_add_item(cfg, section = None, item = None):
        CFG_SECTION_VALUES = '__section_values__'

        if not isinstance(cfg, dict):
            raise ValueError

        subcfg = cfg

        # if section is given, navigate to it
        # if a (sub)section is not found, create it
        if not section is None:
            if isinstance(section, list):
                for s in section:
                    if not s in subcfg:
                        subcfg[s] = {}
                    subcfg = subcfg[s]

            elif isinstance(section, str):
                if not section in cfg:
                    cfg[section] = {}
                subcfg = cfg[section]
            else:
                raise ValueError

        # add item to section
        # if item is a string or a list, add it to list CFG_SECTION_VALUES
        if isinstance(item, list) or isinstance(item, str):
            if isinstance(item, str):
                item = [item]

            if not CFG_SECTION_VALUES in subcfg:
                subcfg[CFG_SECTION_VALUES] = []
            subcfg[CFG_SECTION_VALUES].extend(item)

        # allow the creation of empty sections
        elif item is None and not section is None:
            pass
        else:
            raise ValueError

        # although not necessary, explicitly return modified cfg-dict
        return cfg

    @staticmethod
    def cfg_del_item(cfg, section = None, item = None):
        CFG_SECTION_VALUES = '__section_values__'

        if not isinstance(cfg, dict):
            raise ValueError

        subcfg = cfg
        section_found = True

        # if section is given, navigate to it
        # if a (sub)section is not section_found, abort
        if not section is None:
            if isinstance(section, list):
                for s in section:
                    if not s in subcfg:
                        section_found = False
                        break
                    subcfg = subcfg[s]

            elif isinstance(section, str):
                if not section in cfg:
                    section_found = False
                subcfg = cfg[section]
            else:
                raise ValueError

        # do some final tests, then remove item
        if section_found and CFG_SECTION_VALUES in subcfg and item in subcfg[CFG_SECTION_VALUES]:
            subcfg[CFG_SECTION_VALUES].pop(subcfg[CFG_SECTION_VALUES].index(item))

        # although not necessary, explicitly return modified cfg-dict
        return cfg

    @staticmethod
    def compileZoneFile(cls, nameservers, hosts = None):
        # element in nameservers: tuple(server-name, server-ipaddr, zone that server handles)
        # element in hosts: tuple(server-name, server-ipaddr)

        if nameservers is None:
            nameservers = []

        if hosts is None:
            hosts = []

        nameserverlist = []
        tmpnameserverlist = []
        forwardhostlist = []
        reversehostlist = []

        seen_server_names = {}

        for server_name, server_addr, zone in nameservers:
            if isIPv4Address(server_addr):
                recordtype = 'A'
            elif isIPv6Address(server_addr):
                recordtype = 'AAAA'
            else:
                raise ValueError

            if not server_name in seen_server_names:
                seen_server_names[server_name] = {}
            if not zone in seen_server_names[server_name]:
                seen_server_names[server_name][zone]= 1

            tmpnameserverlist.extend([
                    server_name, ' ', recordtype, ' ', server_addr, '\n'
                    ])

        for servername, zones in seen_server_names.items():
            for zone in zones.keys():
                nameserverlist.extend([zone, ' IN NS ', servername, '\n'])

        nameserverlist.extend(tmpnameserverlist)

        for host_name, host_addr, zone in hosts:
            if isIPv4Address(host_addr):
                recordtype = 'A'
            elif isIPv6Address(host_addr):
                recordtype = 'AAAA'
            else:
                raise ValueError

            forwardhostlist.extend([host_name, ' IN ', recordtype, ' ', host_addr, '\n'])

        return (''.join(nameserverlist), ''.join(forwardhostlist), ''.join(reversehostlist))

    @staticmethod
    def nodewalker_find_root_dns_callback(startnode, currentnode):
        """ add any dns root server to the list of resolvers
        """
        servers = []
        # element in servers: tuple(server-fqdn, server-ipaddr, zone that server handles)

        # check if remote node is a root dns server and
        # we are not ourselves a root server
        if service_flags.DNSRootServer in currentnode.services:
            server_name = '%s' % (currentnode.name)
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    servers.append((server_name, server_addr))

        return servers

    @staticmethod
    def nodewalker_find_root_and_as_dns_callback(startnode, currentnode):
        """ add any dns root server to the list of resolvers and
            add any auth-zone server to the list of that zone-resolvers
        """
        if hasattr(currentnode, 'netid') and not currentnode.netid is None:
            netid = currentnode.netid
        else:
            netid = 0

        servers = []
        # element in servers: tuple(server-fqdn, server-ipaddr, zone that server handles)

        # check if remote node is a root dns server and
        # we are not ourselves a root server
        if service_flags.DNSRootServer in currentnode.services:
            server_name = '%s' % (currentnode.name)

            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    zone = "."
                    servers.append((server_name, server_addr, zone))
                    zone = "virtual."
                    servers.append((server_name, server_addr, zone))

        if service_flags.DNSASRootServer in currentnode.services:
            server_name = currentnode.name
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    zone = "AS%s.virtual." % str(netid)
                    servers.append((server_name, server_addr, zone))

        return servers

    @staticmethod
    def nodewalker_root_dns_find_auth_servers_callback(startnode, currentnode):
        """ add any auth-zone server to the list of that zone-resolver
            exclude servers that are in a differen AS as the start node
        """
        servers = []
        # element in servers: tuple(server-fqdn, server-ipaddr, zone that server handles)

        # check if remote node is an authoritative dns server for an AS and
        # and we are not an authoritative dns server for the same AS

        #        not (service_flags.DNSASRootServer in startnode.services and \
        if service_flags.DNSASRootServer in currentnode.services and \
                currentnode.netid == startnode.netid:

            if hasattr(currentnode, 'netid') and not currentnode.netid is None:
                netid = currentnode.netid
            else:
                # TODO: netid 0 is invalid
                netid = 0

            server_name = currentnode.name
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    zone = "AS%s.virtual." % str(netid)
                    servers.append((server_name, server_addr, zone))

        return servers

    @staticmethod
    def nodewalker_root_dns_find_all_auth_servers_callback(startnode, currentnode):
        """ add any auth-zone server to the list of that zone-resolvers """
        servers = []
        # element in servers: tuple(server-fqdn, server-ipaddr, zone that server handles)

        # check if remote node is an authoritative dns server for an AS
        if service_flags.DNSASRootServer in currentnode.services:

            if hasattr(currentnode, 'netid') and not currentnode.netid is None:
                netid = currentnode.netid
            else:
                # TODO: netid 0 is invalid
                netid = 0

            server_name = currentnode.name
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    zone = "AS%s.virtual." % str(netid)
                    servers.append((server_name, server_addr, zone))

        return servers

    @staticmethod
    def nodewalker_asroot_dns_find_hosts_in_as_callback(startnode, currentnode):
        """ add any host from the AS of startnode to hostlist and return it """
        hosts = []
        # element in hosts: tuple(server-fqdn, server-ipaddr, zone that host lives in)

        if hasattr(currentnode, 'netid') and not currentnode.netid is None:
            netid = currentnode.netid
        else:
            # TODO: netid 0 is invalid
            netid = 0
        zone = "AS%s.virtual." % str(netid)

        # ignore AS authoritative servers as they are already included
        #if not service_flags.DNSASRootServer in currentnode.services and \
        if currentnode.netid == startnode.netid:

            # add plain hostname
            server_name = currentnode.name
            for ipversion in currentnode.getIPversions():
                server_addr = currentnode.getLoopback(ipversion)
                server_addr = str(server_addr).partition('/')[0]
                hosts.append((server_name, server_addr, zone))

            # add all interface names
            for intf in list(currentnode._netif.values()):
                server_name = '%s.%s' % (intf.name, currentnode.name)
                # use first v4 and first v6 address of this interface
                v4addr = None
                v6addr = None
                for addr in intf.addrlist:
                    addr = addr.partition('/')[0]
                    if not v4addr is None and not v6addr is None:
                        break
                    if v4addr is None and isIPv4Address(addr):
                        v4addr = addr
                    if v6addr is None and isIPv6Address(addr):
                        v6addr = addr

                if not v4addr is None:
                    hosts.append((server_name, v4addr, zone))
                if not v6addr is None:
                    hosts.append((server_name, v6addr, zone))

        return hosts

addservice(Bind9)

class Bind9ForwarderAndServer(Bind9):
    """ Bind9-forwarder service """
    _name = "Bind9-forwarder_and_server"
    _meta = "bind dns caching forwarder/resolver service"

    _use_external_resolver = False
    _external_upstream_resolver = "8.8.8.8"

    @staticmethod
    def generateDefaultZonesConf(cls, node, services):
        cfgitems = {}

        cfgitems = cfgitems = super().generateDefaultDefaultZonesConf(cls)
        if service_flags.DNSRootServer in node.services:
            super().cfg_del_item(cfgitems, 'zone "."', 'type hint;')
            super().cfg_del_item(cfgitems, 'zone "."', 'file "/etc/bind/db.root";')

        # check if this DNS server is a pure forwarder
        if cls._use_external_resolver:
            cls.cfg_add_item(cfgitems, 'zone "."', 'type forward;')
            cls.cfg_add_item(cfgitems, ['zone "."', 'forwarders'],
                    '%s%s' % (cls._external_upstream_resolver, ';'))
        elif service_flags.DNSRootServer in node.services:
            cls.cfg_add_item(cfgitems, 'zone "."', 'type master;')
            cls.cfg_add_item(cfgitems, 'zone "."', 'file "/etc/bind/db.root";')

        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateNamedLocalConf(cls, node, services):
        cfgitems = cls.generateDefaultLocalConf(cls)

        if hasattr(node, 'netid') and not node.netid is None:
            netid = node.netid
        else:
            netid = 0

        if service_flags.DNSRootServer in node.services:
            print(('[DEBUG] generating config for DNS Root Server: %s' % node.name))
            # handle zone: virtual. (which serves as root-zone for all virtualized nodes
            cls.cfg_add_item(cfgitems, 'zone "virtual"', 'type master;')
            cls.cfg_add_item(cfgitems, 'zone "virtual"',
                    'file "/etc/bind/db.virtual";')

            # create root zone db
            cls.generateDBAuthoritativeFile(cls, node, '.',
                    cls.nodewalker_find_root_and_as_dns_callback)
            # create virtual. zone db
            cls.generateDBAuthoritativeFile(cls, node, 'virtual.',
                    cls.nodewalker_find_root_and_as_dns_callback,
                    cls.nodewalker_root_dns_find_all_auth_servers_callback)

        else:
            # create root zone db with hints
            cls.generateDBClientFile(cls, node, '.',
                    cls.nodewalker_find_root_and_as_dns_callback)

        if service_flags.DNSASRootServer in node.services:
            print(('[DEBUG] generating config for DNS AS authoritative Server: %s - AS: %d' %
                (node.name, netid)))
            zone = 'AS%s.virtual.' % str(netid)
            # strip '.' at end
            zonefname = zone.rstrip('.')

            # add AS zones to AS-auth-nameservers as master
            cls.cfg_add_item(cfgitems, 'zone "%s"' % zone, 'type master;')
            cls.cfg_add_item(cfgitems, 'zone "%s"' % zone, 'file "/etc/bind/db.%s";' % zonefname)
            cls.generateDBAuthoritativeFile(cls, node, zone,
                    cls.nodewalker_root_dns_find_auth_servers_callback,
                    None,
                    cls.nodewalker_asroot_dns_find_hosts_in_as_callback)

        if service_flags.DNSRootServer in node.services or \
                service_flags.DNSASRootServer in node.services:
            # add reverse lookup PTR records
            ptrzones = cls.getAndGeneratePTRZones(cls, node)
            print(('[DEBUG] getAndGeneratePTRZones() returned ptrzones: %s' % ptrzones))
            for ptrzone in ptrzones:
                print(('[DEBUG] adding ptrzone: %s' % ptrzone))
                ptrzonefname = ptrzone.rstrip('.')
                cls.cfg_add_item(cfgitems, 'zone "%s"' % ptrzone, 'type master;')
                cls.cfg_add_item(cfgitems, 'zone "%s"' % ptrzone, 'file "/etc/bind/db.%s";' % ptrzonefname)

        # xTODO: populate /etc/bind/db.virtual (when done, do we need the forward-section? no. remove it.)
        # xTODO: fix with internal root-servers /etc/bind/db.root
        # xTODO: on AS Auth. Servers: define (cfg) and create/poplule db.AS$foo.virtual, db.reverse
        # xTODO: rueckwaertshochguck
        # xTODO: v6, v6 and v6 (xresolvconf, xroot-hints (force at least one addr to be v6), xdelegates, xPTR
        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateNamedOptionsConf(cls, node, services):
        cfgitems = cls.generateDefaultOptionsConf(cls)
        return cls.compile_named_conf(cls, cfgitems)

addservice(Bind9ForwarderAndServer)

class DNSResolvconf(DNSServices):
    """ dns resolver service for nodes """

    _name = "DNSResolvconf"
    _configs = ("/etc/resolv.conf", )
    _dirs = (("/etc", "union"), )
    _startindex = 1
    _meta = "dns resolver service. generates a resolv.conf for a client"

    @classmethod
    def generateconfig(cls, node, filename, services):
        """ Generate a bind-resolver.sh script """
        if filename == cls._configs[0]:
            return cls.generateResolvconf(node, services)
        else:
            raise ValueError

    @classmethod
    def generateResolvconf(cls, node, services):
        confstr_list = []

        if service_flags.DNSResolver in node.services:
            # if we are a DNS server, add ::1, 127.0.0.1 to resolv.conf
            if node.enable_ipv6:
                confstr_list.append('nameserver ::1\n')
            if node.enable_ipv4:
                confstr_list.append('nameserver 127.0.0.1\n')
        else:
            print('[DNSResolvconf] generating for node: %s' % node.name)
            # add any dns server which is on our AS to the list of resolvers
            list_len = len(confstr_list)
            service_helpers.nodewalker(node, node, confstr_list,
                    cls.nodewalker_Resolver_only_callback)

            print('[DNSResolvconf] found %d resolvers' % len(confstr_list))

            # if no resolvers could be found, also include authoritative AS dns
            if list_len == len(confstr_list):
                list_len = len(confstr_list)
                service_helpers.nodewalker(node, node, confstr_list,
                        cls.nodewalker_Resolver_and_ASAuth_only_callback)
                print('[DNSResolvconf] found %d resolvers and AS auth servers' % len(confstr_list))
                # if no resolvers could be found, also include authoritative AS and root dns
                if list_len == len(confstr_list):
                    service_helpers.nodewalker(node, node, confstr_list,
                            cls.nodewalker_all_DNS_Resolver_callback)
                    print('[DNSResolvconf] found %d resolvers, AS auth and root servers' % len(confstr_list))
        confstr_list.append('search virtual\ndomain virtual\n')

        return ''.join(confstr_list)

    @staticmethod
    def nodewalker_Resolver_only_callback(startnode, currentnode):
        cfgitems = []
        #print(('[DNSResolvconf] startnode: %s, AS: %d, potential node: %s, AS: %d' %
        #        (startnode.name, startnode.netid, currentnode.name, currentnode.netid)))
        # check if remote node is a dns server within our AS
        if service_flags.DNSResolver in currentnode.services and \
                not service_flags.DNSRootServer in currentnode.services and \
                not service_flags.DNSASRootServer in currentnode.services and \
                startnode.netid == currentnode.netid:
            #print(('[DNSResolvconf] startnode: %s, found potential resolver node: %s' %
            #        (startnode.name, currentnode.name)))
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    cfgitems.extend(['nameserver ', server_addr, '\n'])

        return cfgitems

    @staticmethod
    def nodewalker_Resolver_and_ASAuth_only_callback(startnode, currentnode):
        cfgitems = []
        # check if remote node is a dns server within our AS
        if service_flags.DNSResolver in currentnode.services and \
                not service_flags.DNSRootServer in currentnode.services and \
                startnode.netid == currentnode.netid:
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    cfgitems.extend(['nameserver ', server_addr, '\n'])

        return cfgitems

    @staticmethod
    def nodewalker_all_DNS_Resolver_callback(startnode, currentnode):
        cfgitems = []
        # check if remote node is a dns server within our AS
        if service_flags.DNSResolver in currentnode.services and \
                startnode.netid == currentnode.netid:
            for ipversion in currentnode.getIPversions():
                if ipversion in startnode.getIPversions():
                    server_addr = currentnode.getLoopback(ipversion)
                    server_addr = str(server_addr).partition('/')[0]
                    cfgitems.extend(['nameserver ', server_addr, '\n'])

        return cfgitems

addservice(DNSResolvconf)
