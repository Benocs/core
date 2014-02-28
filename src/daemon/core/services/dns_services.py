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

from core.service import CoreService, addservice
from core.misc.ipaddr import IPv4Prefix, IPv6Prefix
from core.misc.ipaddr import isIPv4Address, isIPv6Address
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
            "/etc/bind/named.conf.local", "/etc/bind/named.conf.options")
    _dirs = (("/etc/bind", "union"), ("/var/cache/bind", "bind"),
            ("/var/log", "bind"))
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
            serial = 20140101000000,
            ttl = 900, refresh = 900, retry = 450,
            expire = 3600000, negcache = 900):

        print(('generating SOA header for zone: %s, served by: %s' % (str(zone),
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

        if zone == '.':
            soaitems.append('@ IN SOA %s. root.%s.' % (nameservers[0], nameservers[0]))
        else:
            soaitems.append('@ IN SOA %s.%s root.%s.%s' % (nameservers[0], zone, nameservers[0], zone))
        soaitems.append(' (%d %d %d %d %d)\n' % (serial, refresh, retry, expire, negcache))

        soaitems.append('%s\n' % '\n'.join(list(['  IN NS %s' % x[0] for x in auth_nameservers])))

        return ''.join(soaitems)

    @staticmethod
    def generateDBAuthoritativeFile(cls, node, zone, nodewalker_cb):
        # add any authoritative dns server to the list of resolvers for that AS,
        # if we are not an authoritative dns server for the same AS
        servers = []
        service_helpers.nodewalker(node, node, [], servers, nodewalker_cb)

        # servers managing virtual zone
        virtualservers = []
        for servername, ipaddr, server_zone in servers:
            if server_zone == zone:
                print(('adding to zone: "%s" server: "%s"' % (server_zone, servername)))
                virtualservers.append((servername, ipaddr))

        rawzonecontents = cls.compileZoneFile(cls, list([(x[0], x[1], zone) for x in virtualservers]))[0]
        SOAHeader = cls.generateSOAHeader(cls, virtualservers, zone)
        zonecontents = '%s\n%s' % (SOAHeader, rawzonecontents)
        print(("zone: %s: %s" % (zone, zonecontents)))

        ## TODO: handle the case when two tuples exit with both the same zone

        if len(servers) > 0:
            # rename root-zone from '.' to 'root'
            if zone == '.':
                zone = 'root'
            # strip '.' at end
            zone = zone.rstrip('.')
            # and write result
            node.nodefile('/etc/bind/db.%s' % zone, zonecontents)

    @staticmethod
    def generateDBClientFile(cls, node, zone, nodewalker_cb):
        # add any authoritative dns server to the list of resolvers for that AS,
        # if we are not an authoritative dns server for the same AS
        servers = []
        service_helpers.nodewalker(node, node, [], servers, nodewalker_cb)

        # servers managing virtual zone
        virtualservers = []
        for servername, ipaddr, server_zone in servers:
            if server_zone == zone:
                print(('adding to zone: "%s" server: "%s"' % (server_zone, servername)))
                virtualservers.append((servername, ipaddr))

        zonecontents = cls.compileZoneFile(cls, list([(x[0], x[1], zone) for x in virtualservers]))[0]
        print(("zone: %s: %s" % (zone, zonecontents)))

        ## TODO: handle the case when two tuples exit with both the same zone

        if len(servers) > 0:
            # rename root-zone from '.' to 'root'
            if zone == '.':
                zone = 'root'
            # strip '.' at end
            zone = zone.rstrip('.')
            # and write result
            node.nodefile('/etc/bind/db.%s' % zone, zonecontents)

    @staticmethod
    def generateZoneContent(cls, node, zone, nodewalker_cb):
        # add any authoritative dns server to the list of resolvers for that AS,
        # if we are not an authoritative dns server for the same AS
        servers = []
        service_helpers.nodewalker(node, node, [], servers, nodewalker_cb)

        # servers managing virtual zone
        virtualservers = []
        for servername, ipaddr, server_zone in servers:
            if server_zone == zone:
                print(('adding to zone: "%s" server: "%s"' % (server_zone, servername)))
                virtualservers.append((servername, ipaddr))

        zonecontent = cls.compileZoneFile(cls, [], list([(x[0], x[1], zone) for x in virtualservers]))[1]
        print(("zone: %s: %s" % (zone, zonecontent)))

        ## TODO: handle the case when two tuples exit with both the same zone

        if len(servers) > 0:
            # rename root-zone from '.' to 'root'
            if zone == '.':
                zone = 'root'
            # strip '.' at end
            zone = zone.rstrip('.')
            # and write result
            with node.opennodefile('/etc/bind/db.%s' % zone, mode = 'a') as f:
                f.write(zonecontent)

    @staticmethod
    def generatePTRAuthoritativeFile(cls, node, zone, nodewalker_cb):
        """ build world wide PTR record file. distributing it to AS-nameserver is TODO """

        # TODO:
        """
        root_nameservers = []
        service_helpers.nodewalker(node, node, [], root_nameservers,
                cls.nodewalker_find_root_dns_callback)

        # servers managing virtual zone
        virtualservers = []
        for servername, ipaddr, server_zone in root_nameservers:
            if server_zone == zone:
                print('adding to zone: "%s" server: "%s"' % (server_zone, servername))
                virtualservers.append((servername, ipaddr))

        #####################################

        nodes = []
        service_helpers.nodewalker(node, node, [], nodes, nodewalker_cb)

        # nodes managing virtual zone
        virtualnodes = []
        for servername, ipaddr, server_zone in nodes:
            print('adding to zone: "%s" server: "%s"' % (server_zone, servername))
            virtualnodes.append((servername, ipaddr))

        #rawzonecontent = cls.compileZoneFile(cls, list(map(lambda x: (x[0], x[1], zone), virtualnodes)))[0]
        rawzonecontent = cls.compileZoneFile(cls,
                list(map(lambda x: (x[0], x[1], zone), virtualservers))
                list(map(lambda x: (x[0], x[1], zone), virtualnodes)))

        SOAHeader = cls.generateSOAHeader(cls, virtualnodes, zone)
        zonecontents = '%s\n%s' % (SOAHeader, rawzonecontent)
        print("zone: %s: %s" % (zone, zonecontent))

        ## TODO: handle the case when two tuples exit with both the same zone

        if len(nodes) > 0:
            # rename root-zone from '.' to 'root'
            if zone == '.':
                zone = 'root'
            # strip '.' at end
            zone = zone.rstrip('.')
            # and write result
            node.nodefile('/etc/bind/db.%s' % zone, zonecontents)
        """


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

        if hosts is None:
            hosts = []

        nameserverlist = []
        forwardhostlist = []
        reversehostlist = []

        for server_name, server_addr, zone in nameservers:
            if isIPv4Address(server_addr):
                recordtype = 'A'
            elif isIPv6Address(server_addr):
                recordtype = 'AAAA'
            else:
                raise ValueError

            nameserverlist.extend([
                    zone, ' IN NS ', server_name, '\n',
                    server_name, ' ', recordtype, ' ', server_addr, '\n\n'
                    ])

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
            if len(list(currentnode._netif.values())) > 0 and \
                    len(list(currentnode._netif.values())[0].addrlist) > 0:

                server_name = '%s' % (currentnode.name)
                server_addr = list(currentnode._netif.values())[0].addrlist[0].partition('/')[0]
                zone = "."
                servers.append((server_name, server_addr, zone))
                zone = "virtual."
                servers.append((server_name, server_addr, zone))
                #servers.extend([str(currentnode.getLoopbackIPv4())])

        if service_flags.DNSASRootServer in currentnode.services:
            if len(list(currentnode._netif.values())) > 0 and \
                    len(list(currentnode._netif.values())[0].addrlist) > 0:
                server_name = currentnode.name
                server_addr = list(currentnode._netif.values())[0].addrlist[0].partition('/')[0]
                zone = "AS%s.virtual." % str(netid)
                servers.append((server_name, server_addr, zone))

        return servers

    @staticmethod
    def nodewalker_root_dns_find_auth_servers_callback(startnode, currentnode):
        """ add any dns root server to the list of resolvers and
            add any auth-zone server to the list of that zone-resolvers
        """
        servers = []
        # element in servers: tuple(server-fqdn, server-ipaddr, zone that server handles)

        # check if remote node is an authoritative dns server for an AS and
        # and we are not an authoritative dns server for the same AS

        #        not (service_flags.DNSASRootServer in startnode.services and \
        if service_flags.DNSASRootServer in currentnode.services and \
                currentnode.netid == startnode.netid:
            if len(list(currentnode._netif.values())) > 0 and \
                    len(list(currentnode._netif.values())[0].addrlist) > 0:

                if hasattr(currentnode, 'netid') and not currentnode.netid is None:
                    netid = currentnode.netid
                else:
                    netid = 0

                #server_name = '%s.AS%s.virtual.' % (currentnode.name, str(netid))
                server_name = currentnode.name
                server_addr = list(currentnode._netif.values())[0].addrlist[0].partition('/')[0]
                zone = "AS%s.virtual." % str(netid)
                servers.append((server_name, server_addr, zone))
                #servers.extend([str(currentnode.getLoopbackIPv4())])

        return servers

    @staticmethod
    def nodewalker_asroot_dns_find_hosts_in_as_callback(startnode, currentnode):
        """ add any host from the AS of startnode to hostlist and return it """
        hosts = []
        # element in hosts: tuple(server-fqdn, server-ipaddr, zone that host lives in)

        if hasattr(currentnode, 'netid') and not currentnode.netid is None:
            netid = currentnode.netid
        else:
            netid = 0
        zone = "AS%s.virtual." % str(netid)

        # ignore AS authoritative servers as they are already included
        if not service_flags.DNSASRootServer in currentnode.services and \
                currentnode.netid == startnode.netid:

            # add plain hostname
            if len(list(currentnode._netif.values())) > 0 and \
                    len(list(currentnode._netif.values())[0].addrlist) > 0:
                #hosts.extend([str(currentnode.getLoopbackIPv4())])
                # TODO: switch this addr to loopback as soon as loopback-routing works
                server_name = currentnode.name
                server_addr = list(currentnode._netif.values())[0].addrlist[0].partition('/')[0]
                hosts.append((server_name, server_addr, zone))

            # add all interface names
            for intf in list(currentnode._netif.values()):
                server_name = '%s.%s' % (intf.name, currentnode.name)
                # use first v4 and first v6 address of this interface
                v4addr = None
                v6addr = None
                for addr in intf.addrlist:
                    addr = addr.partition('/')[0]
                    if v4addr is None and isIPv4Address(addr):
                        v4addr = addr
                    if v6addr is None and isIPv6Address(addr):
                        v6addr = addr

                if not v4addr is None:
                    hosts.append((server_name, v4addr, zone))
                if not v6addr is None:
                    hosts.append((server_name, v6addr, zone))

        return hosts

    @staticmethod
    def nodewalker_root_dns_find_all_nodes_callback(startnode, currentnode):
        """ add any host to hostlist and return it """
        hosts = []
        # element in hosts: tuple(server-fqdn, server-ipaddr, zone that host lives in)

        # add plain hostname
        #if len(currentnode._netif.values()) > 0 and \
        #        len(list(currentnode._netif.values())[0].addrlist) > 0:
        #    #hosts.extend([str(currentnode.getLoopbackIPv4())])
        #    # TODO: switch this addr to loopback as soon as loopback-routing works
        #    server_name = currentnode.name
        #    server_addr = list(currentnode._netif.values())[0].addrlist[0].partition('/')[0]
        #    hosts.append((server_name, server_addr, zone))

        # add all interface names
        for intf in list(currentnode._netif.values()):
            server_name = '%s.%s' % (intf.name, currentnode.name)
            # use first v4 and first v6 address of this interface
            v4addr = None
            v6addr = None
            for addr in intf.addrlist:
                addr = addr.partition('/')[0]
                if v4addr is None and isIPv4Address(addr):
                    v4addr = addr
                #if v6addr is None and isIPv6Address(addr):
                #    v6addr = addr

            if not v4addr is None:
                hosts.append((server_name, v4addr, zone))
            #if not v6addr is None:
            #    hosts.append((server_name, v6addr, zone))

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

        if cls._use_external_resolver:
            cls.cfg_add_item(cfgitems, 'zone "."', 'type forward;')
            cls.cfg_add_item(cfgitems, ['zone "."', 'forwarders'],
                    '%s%s' % (cls._external_upstream_resolver, ';'))
        elif service_flags.DNSRootServer in node.services:
            cls.cfg_add_item(cfgitems, 'zone "."', 'type master;')
            cls.cfg_add_item(cfgitems, 'zone "."', 'file "/etc/bind/db.root";')
        #else:
        #    cls.cfg_add_item(cfgitems, 'zone "."', 'type hint;')
        #    cls.cfg_add_item(cfgitems, 'zone "."', 'file "/etc/bind/db.root";')

        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateNamedLocalConf(cls, node, services):
        cfgitems = cls.generateDefaultLocalConf(cls)

        if hasattr(node, 'netid') and not node.netid is None:
            netid = node.netid
        else:
            netid = 0

        if service_flags.DNSRootServer in node.services:
            # handle zone: virtual. (which serves as root-zone for all virtualized nodes
            cls.cfg_add_item(cfgitems, 'zone "virtual"', 'type master;')
            cls.cfg_add_item(cfgitems, 'zone "virtual"',
                    'file "/etc/bind/db.virtual";')

            # create root zone db
            cls.generateDBAuthoritativeFile(cls, node, '.',
                    cls.nodewalker_find_root_dns_callback)
            # create virtual. zone db
            cls.generateDBAuthoritativeFile(cls, node, 'virtual.',
                    cls.nodewalker_find_root_dns_callback)
        else:
            # create root zone db with hints
            cls.generateDBClientFile(cls, node, '.',
                    cls.nodewalker_find_root_dns_callback)

        if service_flags.DNSRootServer in node.services or \
                service_flags.DNSASRootServer in node.services:
            zone = 'AS%s.virtual.' % str(netid)
            # strip '.' at end
            zonefname = zone.rstrip('.')

            # add AS zones to AS-auth-nameservers as master
            #if service_flags.DNSASRootServer in node.services:
            cls.cfg_add_item(cfgitems, 'zone "%s"' % zone, 'type master;')
            cls.cfg_add_item(cfgitems, 'zone "%s"' % zone, 'file "/etc/bind/db.%s";' % zonefname)
            cls.generateDBAuthoritativeFile(cls, node, zone,
                    cls.nodewalker_root_dns_find_auth_servers_callback)

            ## and add AS zones to root nameservers as delegates (hint)
            #elif service_flags.DNSRootServer in node.services:
            #    cls.cfg_add_item(cfgitems, 'zone "%s"' % zone, 'type hint;')
            #    cls.cfg_add_item(cfgitems, 'zone "%s"' % zone, 'file "/etc/bind/db.%s";' % zonefname)
            #    cls.generateDBClientFile(cls, node, zone,
            #            cls.nodewalker_root_dns_find_auth_servers_callback)

            # add reverse lookup PTR records TODO: v6 .in-addr.arpa.
            #if service_flags.DNSRootServer in node.services:
            #    ptrzone = 'in-addr.arpa.'
            #    ptrzonefname = ptrzone.rstrip('.')
            #    cls.cfg_add_item(cfgitems, 'ptrzone "%s"' % ptrzone, 'type master;')
            #    cls.cfg_add_item(cfgitems, 'ptrzone "%s"' % ptrzone, 'file "/etc/bind/db.%s";' % ptrzonefname)
            #    cls.generatePTRAuthoritativeFile(cls, node, ptrzone,
            #            cls.nodewalker_root_dns_find_all_nodes_callback)


            # add hosts that live in this AS to this zone
            if service_flags.DNSASRootServer in node.services:
                cls.generateZoneContent(cls, node, zone,
                        cls.nodewalker_asroot_dns_find_hosts_in_as_callback)

        # xTODO: populate /etc/bind/db.virtual (when done, do we need the forward-section? no. remove it.)
        # xTODO: fix with internal root-servers /etc/bind/db.root
        # xTODO: on AS Auth. Servers: define (cfg) and create/poplule db.AS$foo.virtual, db.reverse
        # TODO: rueckwaertshochguck
        # TODO: v6, v6 and v6 (resolvconf, root-hints (force at least one addr to be v6), delegates, PTR
        return cls.compile_named_conf(cls, cfgitems)

    @staticmethod
    def generateNamedOptionsConf(cls, node, services):
        cfgitems = cls.generateDefaultOptionsConf(cls)
        return cls.compile_named_conf(cls, cfgitems)


addservice(Bind9ForwarderAndServer)

class DNSMasq(DNSServices):
    """ DNSMasq service for nodes """

    _name = "DNSMasq"
    _configs = ("/etc/dnsmasq.conf",
            "/etc/dnsmasq.d/virtual_hosts")
    _dirs = (("/etc", "union"), ("/etc/dnsmasq.d", "bind"))
    #_startindex = 90
    _startup = ("dnsmasq",)
    _shutdown = ("pkill dnsmasq",)
    #_validate = ('pidof "dnsmasq"',)
    _meta = "dns resolver service"

    @classmethod
    def generateconfig(cls, node, filename, services):
        """ Generate a bind-resolver.sh script """
        if filename == cls._configs[0]:
            return cls.generateDNSMasqconf(node, services)
        elif filename == cls._configs[1]:
            return cls.generateVirtualHosts(node, services)
        else:
            raise ValueError

    @classmethod
    def generateDNSMasqconf(cls, node, services):
        use_external_resolver = False
        external_upstream_resolver = "8.8.8.8"

        cfgitems = []

        #if use_internal_upstream_resolver:
        #    cfgitems.append(("server=/virtual./%s\n"%
        #            (internal_upstream_resolver)))
        #elif find_and_use_internal_root_servers:

        # add any dns root server to the list of resolvers
        cfgitemscount = len(cfgitems)
        service_helpers.nodewalker(node, node, [], cfgitems,
                cls.nodewalker_find_root_dns_callback)

        # if no root server could be found, handle everything ourself
        if cfgitemscount == len(cfgitems):
            cfgitems.append("server=/virtual./\n")

        if use_external_resolver:
            cfgitems.append(("server=%s\n" %
                    (external_upstream_resolver)))

        cfgitems.append("domain-needed\n")
        cfgitems.append("localise-queries\n")
        cfgitems.append("read-ethers\n")
        cfgitems.append("expand-hosts\n")
        if service_flags.DNSASRootServer in node.services:
            cfgitems.append("addn-hosts=%s\n" % cls._configs[1])
        cfgitems.append("rebind-localhost-ok\n")

        cfgitems.append("#cache-size=0\n")
        cfgitems.append("#bogus-priv\n")
        cfgitems.append("#resolv-file=/tmp/resolv.conf.auto\n")
        cfgitems.append("#stop-dns-rebind\n")

        if hasattr(node, 'netid') and not node.netid is None:
            netid = node.netid
        else:
            netid = 0

        if service_flags.DNSRootServer in node.services:
            cfgitems.extend([
                    "server=/virtual./\n",
                    "auth-zone=virtual.\n",
                    "domain=virtual.\n"])
            service_helpers.nodewalker(node, node, [], cfgitems,
                    cls.nodewalker_root_dns_callback)
        else:
            cfgitems.append("domain=AS%s.virtual.\n" % netid)

        if service_flags.DNSASRootServer in node.services:
            cfgitems.append("server=/AS%s.virtual./\n" % netid)
            if len(list(node._netif.values())) > 0:
                intflist = []
                for intf in list(node._netif.values()):
                    intflist.append(intf.name)
                    if intf.addrlist > 0:
                        for addr in intf.addrlist:
                            cfgitems.extend(["host-record=AS%s.virtual," % netid,
                                    addr.partition('/')[0], '\n'])
                cfgitems.extend(["auth-server=", node.name, ".AS", str(netid),
                        ".virtual,", ','.join(intflist), '\n',])
                cfgitems.extend(["auth-zone=AS%s.virtual," % netid,
                        ','.join(intflist), '\n'])
        """
        server=/AS100.virtual./
        auth-server=DT-ns-217-0-117-34.AS100.virtual,eth0
        auth-zone=AS100.virtual

        domain=AS100.virtual.
        server=/AS100.virtual./
        auth-server=DT-ns-217-0-117-34.AS100.virtual,eth0
        host-record=AS100.virtual,eth0
        auth-zone=AS100.virtual,eth0

        domain=AS100.virtual.
        server=/AS100.virtual./
        host-record=AS100.virtual,217.0.117.34
        auth-server=DT-ns-217-0-117-34.AS100.virtual,eth0
        auth-zone=AS100.virtual,eth0
        """

        return ''.join(cfgitems)

    @staticmethod
    def nodewalker_find_root_dns_callback(startnode, currentnode):
        """ add any dns root server to the list of resolvers and
            add any auth-zone server to the list of that zone-resolvers
        """
        cfgitems = []

        # check if remote node is a root dns server and
        # we are not ourselves a root server
        if service_flags.DNSRootServer in currentnode.services and \
                not service_flags.DNSRootServer in startnode.services:
            if len(list(currentnode._netif.values())) > 0 and \
                    len(list(currentnode._netif.values())[0].addrlist) > 0:
                cfgitems.extend(['server=/virtual./',
                        list(currentnode._netif.values())[0].addrlist[0].partition('/')[0],
                        '\n',
                        'server=/arpa./',
                        list(currentnode._netif.values())[0].addrlist[0].partition('/')[0],
                        '\n'])
            #cfgitems.extend([str(currentnode.getLoopbackIPv4())])

        if service_flags.DNSRootServer in startnode.services:
            # check if remote node is an authoritative dns server for an AS and
            # and we are not an authoritative dns server for the same AS
            if service_flags.DNSASRootServer in currentnode.services and \
                    not (service_flags.DNSASRootServer in startnode.services and \
                            currentnode.netid == startnode.netid):
                if len(list(currentnode._netif.values())) > 0 and \
                        len(list(currentnode._netif.values())[0].addrlist) > 0:
                    asnumber = currentnode.netid
                    if asnumber is None:
                        asnumber = 0
                    cfgitems.extend(['server=/AS%s.virtual./' % str(asnumber),
                            list(currentnode._netif.values())[0].addrlist[0].partition('/')[0],
                            '\n'])
                #cfgitems.extend([str(currentnode.getLoopbackIPv4())])

        return cfgitems

    @staticmethod
    def nodewalker_root_dns_callback(startnode, currentnode):
        """ add any dns root server to the list of resolvers and """
        cfgitems = []

        # check if remote node is an authoritative dns server for an AS and
        # and we are not an authoritative dns server for the same AS
        if service_flags.DNSASRootServer in currentnode.services and \
                not (service_flags.DNSASRootServer in startnode.services and \
                        currentnode.netid == startnode.netid):
            # define reverse lookup zones/addresses to delegate to that AS
            # authoritative DNS server.
            #
            # this is a two-step process:
            # 1) collect all loopback ip's of this AS
            # 1.1) aggregate found addresses as much as possible -- this is TODO
            if 'ipaddrs' in CONFIGS and 'loopback_net' in CONFIGS['ipaddrs'] and \
                    len(CONFIGS['ipaddrs']['loopback_net'].split('/')) == 2 and \
                    'loopback_net_per_netid' in CONFIGS['ipaddrs']:
                # loopback_net_per_netid
                global_loopback_prefix_str = CONFIGS['ipaddrs']['loopback_net']
                global_prefixbase, global_prefixlen = global_loopback_prefix_str.split('/')
                try:
                    global_prefixlen = int(global_prefixlen)
                except ValueError:
                    return None
                # local means per netid (e.g., AS)
                try:
                    local_prefixlen = int(CONFIGS['ipaddrs']['loopback_net_per_netid'])
                except ValueError:
                    return None

                if hasattr(currentnode, 'netid') and not currentnode.netid is None:
                    netid = currentnode.netid
                else:
                    netid = 0

                global_loopback_prefix = IPv4Prefix(global_loopback_prefix_str)

                baseprefix = IPv4Prefix('%s/%d' % (global_prefixbase, local_prefixlen))
                target_network_baseaddr = baseprefix.minaddr() + (netid * (baseprefix.numaddr() + 2))
                target_network_prefix = IPv4Prefix('%s/%d' % (target_network_baseaddr, local_prefixlen))
                target_network_broadcastaddr = target_network_prefix.maxaddr() + 1

                subnet_prefixlen = 24
                if subnet_prefixlen > local_prefixlen:
                    subnet_prefix = IPv4Prefix('%s/%d' % (target_network_baseaddr, subnet_prefixlen))
                    while subnet_prefix.minaddr() < target_network_broadcastaddr:
                        subnet_list = str(subnet_prefix.minaddr() - 1).split('.')
                        subnet_list.reverse()
                        if len(list(currentnode._netif.values())) > 0 and \
                                len(list(currentnode._netif.values())[0].addrlist) > 0:
                            cfgitems.extend(['server=/', '.'.join(subnet_list[1:]),
                                    '.in-addr.arpa./',
                                    list(currentnode._netif.values())[0].addrlist[0].partition('/')[0],
                                    '\n'])
                            #cfgitems.extend([str(currentnode.getLoopbackIPv4())])
                        # go to next subnet based on prefix length (subnet_prefixlen)
                        subnet_prefix = IPv4Prefix('%s/%d' %
                                ((subnet_prefix.minaddr() - 1) + subnet_prefix.numaddr() + 2,
                                subnet_prefixlen))

            # 2) collect all interface ip addresses of this AS
            # 2.1) aggregate found addresses as much as possible -- this is also TODO
            service_helpers.nodewalker(currentnode, currentnode, [], cfgitems,
                    DNSMasq.nodewalker_find_as_local_intf_addrs_callback)

        return cfgitems

    @staticmethod
    def nodewalker_find_as_local_intf_addrs_callback(startnode, currentnode):
        cfgitems = []
        # check if the remote node is within the same AS as the name server
        # if true, add PTR delegation records
        if startnode.netid == currentnode.netid:
            # add interfaces
            for intf in list(currentnode._netif.values()):
                for addr in intf.addrlist:
                    # TODO: no support for v6 yet
                    if isIPv6Address(addr):
                        continue
                    if hasattr(currentnode, 'netid') and not currentnode.netid is None:
                        netid = currentnode.netid
                    else:
                        netid = 0
                    addr_list = str(addr).split('/')[0].split('.')
                    addr_list.reverse()

                    if len(list(startnode._netif.values())) > 0 and \
                            len(list(startnode._netif.values())[0].addrlist) > 0:
                        cfgitems.extend(['server=/', '.'.join(addr_list),
                                '.in-addr.arpa./',
                                list(startnode._netif.values())[0].addrlist[0].partition('/')[0],
                                '\n'])

                        #cfgitems = [str(currentnode.getLoopbackIPv4())]
        return cfgitems

    @classmethod
    def generateVirtualHosts(cls, node, services):
        cfgitems = []

        if service_flags.DNSASRootServer in node.services:
            # add any host within our AS and add it to the domain db
            service_helpers.nodewalker(node, node, [], cfgitems,
                    cls.nodewalker_virtual_hosts_callback)

        return ''.join(cfgitems)

    @staticmethod
    def nodewalker_virtual_hosts_callback(startnode, currentnode):
        cfgitems = []
        # check if either we are a root server or if remote node is within our AS
        #if service_flags.DNSRootServer in startnode.services or \
        #        startnode.netid == currentnode.netid:

        # check if the remote node is within our AS
        # if true, add A (and, thanks to dnsmasq, thus implicitly PTR records)
        if startnode.netid == currentnode.netid:
            # add loopback
            asnumber = currentnode.netid
            if asnumber is None:
                asnumber = 0
            cfgitems.append('%s %s.AS%s.virtual.\n' % (str(currentnode.getLoopbackIPv4()),
                    currentnode.name, str(asnumber)))
            # add interfaces
            for intf in list(currentnode._netif.values()):
                for addr in intf.addrlist:
                    # TODO: no support for v6 yet
                    if isIPv6Address(addr):
                        continue
                    asnumber = currentnode.netid
                    if asnumber is None:
                        asnumber = 0
                    cfgitems.append('%s %s.%s.AS%s.virtual.\n' % (addr.partition('/')[0],
                            intf.name, currentnode.name, str(asnumber)))

            #cfgitems = [str(currentnode.getLoopbackIPv4())]
        return cfgitems

addservice(DNSMasq)

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
            # if we are a DNS server, add 127.0.0.1 to resolv.conf
            confstr_list.append('nameserver 127.0.0.1\n')
        else:
            # add any dns server which is on our AS to the list of resolvers
            service_helpers.nodewalker(node, node, [], confstr_list, cls.nodewalker_callback)
        confstr_list.append('search virtual\ndomain virtual\n')

        return ''.join(confstr_list)

    @staticmethod
    def nodewalker_callback(startnode, currentnode):
        cfgitems = []
        # check if remote node is a dns server within our AS
        if service_flags.DNSResolver in currentnode.services and \
                startnode.netid == currentnode.netid:
            if len(list(currentnode._netif.values())) > 0 and \
                    len(list(currentnode._netif.values())[0].addrlist) > 0:
                cfgitems = ['nameserver ',
                        list(currentnode._netif.values())[0].addrlist[0].partition('/')[0],
                        '\n']
            #cfgitems = ['nameserver ', str(currentnode.getLoopbackIPv4()), '\n']
        return cfgitems

addservice(DNSResolvconf)
