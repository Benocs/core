#
# topology - classes for building and managing network topologies
#            without needing to have a connection to a core-session
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import pprint

from core.constants import *

from core.misc.ipaddr import IPAddr, IPv4Addr, IPv6Addr
from core.misc.ipaddr import IPPrefix, IPv4Prefix, IPv6Prefix
from core.misc.ipaddr import isIPAddress, isIPv4Address, isIPv6Address

from core.misc import ipaddr
from core.misc.netid import NetIDSubnetMap

from coretopogen.nodes import *

class Topology():
    __meta__ = None
    __nodes__ = None
    __links__ = None

    __bookkeeping__ = None
    __nodes_augmentations__ = None


    netid_subnet_map = NetIDSubnetMap

    # set node-model to match model in nodes.conf - this specifies defaults
    __nodemodel_map__ = {
            'AS_NODE': { 'class': ASNode, 'model': 'egp_node', 'tag': 'egp' },
            'RT_NODE': { 'class': ASNode, 'model': 'igp_node', 'tag': 'igp' },
            'RT_BORDER': { 'class': ASNode, 'model': 'egp_node', 'tag': 'egp' },
            }

    # read ipaddrs.conf, set mapping
    __ipaddrs__ = {
            'ipv4_loopback_net': ipaddr.Loopback.getLoopbackNet(4),
            'ipv4_loopback_net_per_netid': ipaddr.Loopback.getLoopbackNet_per_net(0, 4).prefixlen,
            'ipv4_interface_net': ipaddr.Interface.getInterfaceNet(4),
            'ipv4_interface_net_per_netid': ipaddr.Interface.getInterfaceNet_per_net(0, 4).prefixlen,
            # default
            'ipv4_interface_net_per_ptp_link': 30,
            # default
            'ipv4_interface_net_per_brdcst_link': 24,

            'ipv6_loopback_net': ipaddr.Loopback.getLoopbackNet(4),
            'ipv6_loopback_net_per_netid': ipaddr.Loopback.getLoopbackNet_per_net(0, 6).prefixlen,
            'ipv6_interface_net': ipaddr.Interface.getInterfaceNet(6),
            'ipv6_interface_net_per_netid': ipaddr.Interface.getInterfaceNet_per_net(0, 6).prefixlen,
            # default
            'ipv6_interface_net_per_ptp_link': 63,
            #default
            'ipv6_interface_net_per_brdcst_link': 56,
            }
    if 'ipaddrs' in CONFIGS:
        if 'ipv4_interface_net_per_ptp_link' in CONFIGS['ipaddrs']:
            __ipaddrs__['ipv4_interface_net_per_ptp_link'] = \
                    CONFIGS['ipaddrs']['ipv4_interface_net_per_ptp_link']
        if 'ipv4_interface_net_per_brdcst_link' in CONFIGS['ipaddrs']:
            __ipaddrs__['ipv4_interface_net_per_brdcst_link'] = \
                    CONFIGS['ipaddrs']['ipv4_interface_net_per_brdcst_link']
        if 'ipv6_interface_net_per_ptp_link' in CONFIGS['ipaddrs']:
            __ipaddrs__['ipv6_interface_net_per_ptp_link'] = \
                    CONFIGS['ipaddrs']['ipv6_interface_net_per_ptp_link']
        if 'ipv6_interface_net_per_brdcst_link' in CONFIGS['ipaddrs']:
            __ipaddrs__['ipv6_interface_net_per_brdcst_link'] = \
                    CONFIGS['ipaddrs']['ipv6_interface_net_per_brdcst_link']

    def __init__(self):
        # internal variable for keeping states, global counters, ...
        ipv4_placeholder_addr_str = '192.168.1.0'
        ipv6_placeholder_addr_str = 'fe80::'
        self.__bookkeeping__ = {
                'ipv4_addr_lower_bound': self.__ipaddrs__['ipv4_interface_net'].minaddr(),
                'ipv4_addr_upper_bound': self.__ipaddrs__['ipv4_interface_net'].maxaddr(),
                'ipv4_addresses_per_ptp_link': \
                        IPv4Prefix(('%s/%s' % (\
                            ipv4_placeholder_addr_str, \
                            self.__ipaddrs__['ipv4_interface_net_per_ptp_link'])) \
                            ).prefix.num_addresses,
                'ipv4_addresses_per_brdcst_link': \
                        IPv4Prefix(('%s/%s' % (\
                            ipv4_placeholder_addr_str, \
                            self.__ipaddrs__['ipv4_interface_net_per_brdcst_link'])) \
                            ).prefix.num_addresses,
                'ipv6_addr_lower_bound': self.__ipaddrs__['ipv6_interface_net'].minaddr(),
                'ipv6_addr_upper_bound': self.__ipaddrs__['ipv6_interface_net'].maxaddr(),
                'ipv6_addresses_per_ptp_link': \
                        IPv6Prefix(('%s/%s' % (\
                            ipv6_placeholder_addr_str, \
                            self.__ipaddrs__['ipv6_interface_net_per_ptp_link'])) \
                            ).prefix.num_addresses,
                'ipv6_addresses_per_brdcst_link': \
                        IPv6Prefix(('%s/%s' % (\
                            ipv6_placeholder_addr_str, \
                            self.__ipaddrs__['ipv6_interface_net_per_brdcst_link'])) \
                            ).prefix.num_addresses,
                # key: ASN, value: number of assigned links within an AS
                'ipv4_as_ptp_max_link' : {},
                'ipv6_as_ptp_max_link' : {},
                'ipv4_as_brdcst_max_link' : {},
                'ipv6_as_brdcst_max_link' : {},

                # key: base_node (e.g, igp_node), value: highest used address
                'ipv4_brdcst_max_addr': {},
                # key: base_node (e.g, igp_node), value: highest used address
                'ipv6_brdcst_max_addr': {},
                }

        #pp = pprint.PrettyPrinter(indent=4)
        #print('[DEBUG] bookkeeping contents: ')
        #pp.pprint(self.__bookkeeping__)

        #print('[DEBUG] CONF contents: ')
        #pp.pprint(CONFIGS)

        self.__meta__ = {}
        self.__nodes__ = {}
        self.__links__ = []
        # if a node gets augmented (e.g., an access-network is connected to it),
        # then this dict will contain the key, value-pair (node, [augtype0, augtype1, ...])
        self.__nodes_augmentations__ = {}

    def set_nodemap(self, nodemap):
        print(('[DEBUG] old nodemap: %s' % str(self.__nodemodel_map__)))
        print(('[DEBUG] setting new nodemap: %s' % str(nodemap)))
        self.__nodemodel_map__ = nodemap

    def __as_get_next_link_ipv6_prefix__(self, asn=1, ptp=True):
        #raise NotImplementedError

        def get_as_addrs(asn):
            base_prefix = IPv6Prefix('%s/%s' % (str(self.__ipaddrs__['ipv6_interface_net'].prefix.network_address),
                str(self.__ipaddrs__['ipv6_interface_net_per_netid'])))
            base_addr = IPv6Addr(str(self.__ipaddrs__['ipv6_interface_net'].prefix.network_address))

            # calculate base addr for this AS
            as_base_prefix = ipaddr.Interface.getInterfaceNet_per_net(asn, 6)
            as_base_addr = IPv6Addr(as_base_prefix.prefix.network_address)

            as_prefix = IPv6Prefix('%s/%s' % (str(as_base_addr),
                self.__ipaddrs__['ipv6_interface_net_per_netid']))
            as_upper_addr = IPv6Addr(as_prefix.prefix.broadcast_address)

            #print('[DEBUG] base prefix: %s' % str(base_prefix))
            #print('[DEBUG] base prefix num addr: %s' % str(base_prefix.prefix.num_addresses))
            #print('[DEBUG] ASN - 1: %d' % (asn - 1))
            #rint('[DEBUG] AS base addr: %s' % str(as_base_addr))
            #print('[DEBUG] as_prefix: %s' % str(as_prefix))
            #print('[DEBUG] base addr: %s' % str(base_addr))
            #print('[DEBUG] AS upper addr: %s' % str(as_upper_addr))
            return as_prefix, as_base_addr, as_upper_addr

        def get_next_as_link_number(asn, ptp):
            if ptp:
                key = 'ipv6_as_ptp_max_link'
            else:
                key = 'ipv6_as_brdcst_max_link'

            if not asn in self.__bookkeeping__[key]:
                self.__bookkeeping__[key][asn] = 0
            else:
                self.__bookkeeping__[key][asn] += 1

            return self.__bookkeeping__[key][asn]

        def get_link_prefix(as_base_addr, as_upper_addr, as_link_number, ptp):
            if ptp:
                ipv6_addresses_per_link = 'ipv6_addresses_per_ptp_link'
                ipv6_interface_net_per_link = 'ipv6_interface_net_per_ptp_link'
                link_base_addr = IPv6Addr(as_base_addr.addr +
                        (self.__bookkeeping__[ipv6_addresses_per_link] * as_link_number))
            else:
                ipv6_addresses_per_link = 'ipv6_addresses_per_brdcst_link'
                ipv6_interface_net_per_link = 'ipv6_interface_net_per_brdcst_link'
                link_base_addr = IPv6Addr(as_upper_addr.addr -
                        (self.__bookkeeping__[ipv6_addresses_per_link] * as_link_number))

            link_prefix = IPv6Prefix('%s/%s' % (str(link_base_addr),
                str(self.__ipaddrs__[ipv6_interface_net_per_link])))

            #print('[DEBUG] link_base_addr: %s' % str(link_base_addr))
            #print('[DEBUG] link_prefix: %s' % str(link_prefix))
            return link_prefix

        as_prefix, as_base_addr, as_upper_addr = get_as_addrs(asn)
        as_link_number = get_next_as_link_number(asn, ptp)
        #print('[DEBUG] as_link_number: %s' % str(as_link_number))

        link_prefix = get_link_prefix(as_base_addr, as_upper_addr,
                as_link_number, ptp)

        # some sanity checks
        #sanity_checks(link_prefix, as_prefix)

        return link_prefix

    def __as_get_next_link_ipv4_prefix__(self, asn=1, ptp=True):

        def get_as_addrs(asn):
            base_prefix = IPv4Prefix('%s/%s' % (str(self.__ipaddrs__['ipv4_interface_net'].prefix.network_address),
                str(self.__ipaddrs__['ipv4_interface_net_per_netid'])))
            base_addr = IPv4Addr(str(self.__ipaddrs__['ipv4_interface_net'].prefix.network_address))

            # calculate base addr for this AS
            as_base_prefix = ipaddr.Interface.getInterfaceNet_per_net(asn, 4)
            as_base_addr = IPv4Addr(as_base_prefix.prefix.network_address)
            #print('[DEBUG] base prefix: %s' % str(base_prefix))
            #print('[DEBUG] base prefix num addr: %s' % str(base_prefix.prefix.num_addresses))
            #print('[DEBUG] ASN - 1: %d' % (asn - 1))
            #print('[DEBUG] base addr: %s' % str(base_addr))
            #print('[DEBUG] AS base addr: %s' % str(as_base_addr))

            as_prefix = IPv4Prefix('%s/%s' % (str(as_base_addr),
                self.__ipaddrs__['ipv4_interface_net_per_netid']))
            #print('[DEBUG] as_prefix: %s' % str(as_prefix))
            as_upper_addr = IPv4Addr(as_prefix.prefix.broadcast_address)
            #print('[DEBUG] AS upper addr: %s' % str(as_upper_addr))
            return as_prefix, as_base_addr, as_upper_addr

        def get_next_as_link_number(asn, ptp):
            if ptp:
                key = 'ipv4_as_ptp_max_link'
            else:
                key = 'ipv4_as_brdcst_max_link'

            if not asn in self.__bookkeeping__[key]:
                self.__bookkeeping__[key][asn] = 0
            else:
                self.__bookkeeping__[key][asn] += 1

            return self.__bookkeeping__[key][asn]

        def get_link_prefix(as_base_addr, as_upper_addr, as_link_number, ptp):
            if ptp:
                ipv4_addresses_per_link = 'ipv4_addresses_per_ptp_link'
                ipv4_interface_net_per_link = 'ipv4_interface_net_per_ptp_link'
                link_base_addr = IPv4Addr(as_base_addr.addr +
                        (self.__bookkeeping__[ipv4_addresses_per_link] * as_link_number))
            else:
                ipv4_addresses_per_link = 'ipv4_addresses_per_brdcst_link'
                ipv4_interface_net_per_link = 'ipv4_interface_net_per_brdcst_link'
                link_base_addr = IPv4Addr(as_upper_addr.addr -
                        (self.__bookkeeping__[ipv4_addresses_per_link] * as_link_number))

            link_prefix = IPv4Prefix('%s/%s' % (str(link_base_addr),
                str(self.__ipaddrs__[ipv4_interface_net_per_link])))

            #print('[DEBUG] link_base_addr: %s' % str(link_base_addr))
            #print('[DEBUG] link_prefix: %s' % str(link_prefix))
            return link_prefix

        def sanity_checks(link_prefix, as_prefix):
            if link_prefix.minaddr() < self.__bookkeeping__['ipv4_addr_lower_bound']:
                raise ValueError('link prefix is below global lower bound: %s < %s' % \
                        (str(link_prefix.minaddr()),
                        str(self.__bookkeeping__['ipv4_addr_lower_bound'])))

            if link_prefix.maxaddr() > self.__bookkeeping__['ipv4_addr_upper_bound']:
                raise ValueError('link prefix exceeds global upper bound: %s > %s' % \
                        (str(link_prefix.maxaddr()),
                        str(self.__bookkeeping__['ipv4_addr_upper_bound'])))

            if link_prefix.minaddr() < as_prefix.minaddr():
                raise ValueError('link prefix is below AS lower bound: %s < %s' % \
                        (str(link_prefix.minaddr()),
                        str(as_prefix.minaddr())))

            if link_prefix.maxaddr() > as_prefix.maxaddr():
                raise ValueError('link prefix exceeds AS upper bound: %s > %s' % \
                        (str(link_prefix.maxaddr()),
                        str(as_prefix.maxaddr())))

        as_prefix, as_base_addr, as_upper_addr = get_as_addrs(asn)
        as_link_number = get_next_as_link_number(asn, ptp)
        #print('[DEBUG] as_link_number: %s' % str(as_link_number))

        link_prefix = get_link_prefix(as_base_addr, as_upper_addr,
                as_link_number, ptp)

        # some sanity checks
        sanity_checks(link_prefix, as_prefix)

        return link_prefix

    def add_meta(self, key, value):
        self.__meta__[key] = value

    def get_meta(self, key):
        if key in self.__meta__:
            return self.__meta__[key]
        return None

    def add_node(self, name, node):
        self.__nodes__[name] = node

    def get_node(self, name):
        if name in self.__nodes__:
            return self.__nodes__[name]
        return None

    def get_nodes(self):
        return self.__nodes__

    def get_node_count(self):
        return len(self.__nodes__)

    def get_node_mapping(self, model):
        if model in self.__nodemodel_map__:
            return self.__nodemodel_map__[model]
        return None

    def add_augmented_node(self, node, augmentation_type):
        if not node in self.__nodes_augmentations__:
            self.__nodes_augmentations__[node] = []
        if not augmentation_type in self.__nodes_augmentations__[node]:
            self.__nodes_augmentations__[node].append(augmentation_type)

    def get_non_augmented_nodes(self):
        return [node for node in self.__nodes__.values() if not node in
                self.__nodes_augmentations__]

    def add_link(self, link):
        def is_ptp(link):
            return (not link.get_src_node().get_type() == 'lanswitch' and \
                    not link.get_dst_node().get_type() == 'lanswitch')

        # TODO: refactor me

        #print('[TRACE] add_link(link=%s)' % str(link))
        # TODO: raise if link_cnt > 255 / if addr > ipv4_interface_net/'ipv4_interface_net_per_netid'

        asn = link.get_src_node().get_asn()
        #print('[DEBUG] ASN of src_node: %d' % asn)
        ptp = is_ptp(link)
        #print('[DEBUG] is PTP: %s' % ptp)

        # generate which interfaces
        generate_src_if = False
        src_interface = link.get_src_interface()
        generate_dst_if = False
        dst_interface = link.get_dst_interface()
        src_if_ipv4_addr = None
        dst_if_ipv4_addr = None
        src_if_ipv6_addr = None
        dst_if_ipv6_addr = None

        # case: both interfaces of this link have no addresses set
        if link.get_src_interface() is None or link.get_dst_interface() is None:
            if ptp:
                link_ipv4_prefix = self.__as_get_next_link_ipv4_prefix__(asn, ptp=ptp)
                #print('[DEBUG] ipv4 link_prefix: %s' % str(link_ipv4_prefix))
                src_if_ipv4_addr = link_ipv4_prefix.minaddr()
                src_if_ipv4_addr.set_prefixlen(link_ipv4_prefix.prefixlen)
                dst_if_ipv4_addr = link_ipv4_prefix.maxaddr()
                dst_if_ipv4_addr.set_prefixlen(link_ipv4_prefix.prefixlen)

                link_ipv6_prefix = self.__as_get_next_link_ipv6_prefix__(asn)
                #print('[DEBUG] ipv6 link_prefix: %s' % str(link_ipv6_prefix))
                src_if_ipv6_addr = link_ipv6_prefix.minaddr()
                src_if_ipv6_addr.set_prefixlen(link_ipv6_prefix.prefixlen)

                # when using >=/64 for ptp-links, use next line
                if link_ipv6_prefix.prefixlen >= 64:
                    #dst_if_ipv6_addr = link_ipv6_prefix.maxaddr()
                    dst_if_ipv6_addr = src_if_ipv6_addr + 1
                    dst_if_ipv6_addr.set_prefixlen(link_ipv6_prefix.prefixlen)
                else:
                    # when using </64 (63,62,..) for ptp-links, use next line
                    dst_prefix = IPv6Prefix('%s/%s' % (str(src_if_ipv6_addr),
                            str(link_ipv6_prefix.prefixlen + 1)))
                    # intentionally overflow to next prefix
                    # (skip brdcst, network, select first addr of following prefix)
                    dst_if_ipv6_addr = dst_prefix.maxaddr() + 3
                    dst_if_ipv6_addr.set_prefixlen(link_ipv6_prefix.prefixlen)

                if link.get_src_interface() is None:
                    generate_src_if = True
                if link.get_dst_interface() is None:
                    generate_dst_if = True
            else:
                # not point-to-point-link
                # this means, that there is a switch between src and dst
                # find igp_node (router) behind the switch and use it's subnet
                # as address space for connected nodes
                switch = None
                if link.get_src_node().get_type() == 'lanswitch':
                    switch = link.get_src_node()
                    generate_dst_if = True
                elif link.get_dst_node().get_type() == 'lanswitch':
                    switch = link.get_dst_node()
                    generate_src_if = True

                # give me all links that this switch currently has
                for node_link in self.get_links_of_node(switch):
                    for node, interface in node_link.nodes:
                        if node is switch:
                            continue
                        # found the igp_node (router) behind the switch
                        if node.get_tag() == 'igp':
                            if len(interface.get_addresses()) == 1 and \
                                    interface.get_addresses()[0] is None:
                                #print('[DEBUG] igp_node does not yet have an addr on its interface')
                                pass
                            else:
                                # TODO: this is kinda wrong. what happens when there are more than
                                # one addresses assigned?
                                for base_addr in interface.get_addresses():
                                    ifc_key = interface.get_key()
                                    #print('[DEBUG] base addr of igp_node (if idx: %s) behind switch: %s'
                                    #        % (ifc_key, base_addr))
                                    if isIPv4Address(base_addr):
                                        # set src and dst to the same addr (we only assign one of them. see below)
                                        if not node in self.__bookkeeping__['ipv4_brdcst_max_addr']:
                                            self.__bookkeeping__['ipv4_brdcst_max_addr'][node] = {}
                                        if not ifc_key in self.__bookkeeping__['ipv4_brdcst_max_addr'][node]:
                                            self.__bookkeeping__['ipv4_brdcst_max_addr'][node][ifc_key] = base_addr

                                        self.__bookkeeping__['ipv4_brdcst_max_addr'][node][ifc_key] += 1
                                        src_if_ipv4_addr = self.__bookkeeping__['ipv4_brdcst_max_addr'][node][ifc_key]
                                        src_if_ipv4_addr.set_prefixlen(base_addr.prefixlen)
                                        dst_if_ipv4_addr = src_if_ipv4_addr
                                    elif isIPv6Address(base_addr):
                                        # set src and dst to the same addr (we only assign one of them. see below)
                                        if not node in self.__bookkeeping__['ipv6_brdcst_max_addr']:
                                            self.__bookkeeping__['ipv6_brdcst_max_addr'][node] = {}
                                        if not ifc_key in self.__bookkeeping__['ipv6_brdcst_max_addr'][node]:
                                            self.__bookkeeping__['ipv6_brdcst_max_addr'][node][ifc_key] = base_addr
                                        self.__bookkeeping__['ipv6_brdcst_max_addr'][node][ifc_key] += 1
                                        src_if_ipv6_addr = self.__bookkeeping__['ipv6_brdcst_max_addr'][node][ifc_key]
                                        src_if_ipv6_addr.set_prefixlen(base_addr.prefixlen)
                                        dst_if_ipv6_addr = src_if_ipv6_addr

                if len(self.get_links_of_node(switch)) == 0:
                    #print('[DEBUG] switch does not yet have any registered links')
                    link_ipv4_prefix = self.__as_get_next_link_ipv4_prefix__(asn, ptp=ptp)
                    #print('[DEBUG] ipv4 link_prefix: %s' % str(link_ipv4_prefix))

                    # set src and dst to the same addr (we only assign one of them. see below)
                    src_if_ipv4_addr = link_ipv4_prefix.minaddr()
                    src_if_ipv4_addr.set_prefixlen(link_ipv4_prefix.prefixlen)
                    dst_if_ipv4_addr = src_if_ipv4_addr

                    link_ipv6_prefix = self.__as_get_next_link_ipv6_prefix__(asn, ptp=ptp)
                    #print('[DEBUG] ipv6 link_prefix: %s' % str(link_ipv6_prefix))
                    src_if_ipv6_addr = link_ipv6_prefix.minaddr()
                    src_if_ipv6_addr.set_prefixlen(link_ipv6_prefix.prefixlen)
                    dst_if_ipv6_addr = src_if_ipv6_addr

        if generate_src_if:
            #print('[DEBUG] link: src ipv4 address: %s/%s' % (src_if_ipv4_addr,
            #        str(src_if_ipv4_addr.get_prefixlen())))
            #print('[DEBUG] link: src ipv6 address: %s/%s' % (src_if_ipv6_addr,
            #        str(src_if_ipv6_addr.get_prefixlen())))

            # don't assign an IP address to a switch interface
            if link.get_src_node().get_type() == 'lanswitch':
                #print('[DEBUG] node type is lanswitch')
                src_interface = link.get_src_node().create_interface([])
            else:
                src_interface = link.get_src_node().create_interface([
                    src_if_ipv4_addr, src_if_ipv6_addr])
            #print('[DEBUG] adding link_src: (%s, %s)' % (link.get_src_node().get_name(), src_interface))
            link.set_src(link.get_src_node(), src_interface)

        if src_interface is None:
            #print('[DEBUG] src_interface is None: %s' % str(src_interface))
            src_interface = link.get_src_node().create_interface([])
            link.set_src(link.get_src_node(), src_interface)

        if generate_dst_if:
            #print('[DEBUG] link: dst ipv4 address: %s/%s' % (dst_if_ipv4_addr,
            #        str(dst_if_ipv4_addr.get_prefixlen())))
            #print('[DEBUG] link: dst ipv6 address: %s/%s' % (dst_if_ipv6_addr,
            #        str(dst_if_ipv6_addr.get_prefixlen())))

            # don't assign an IP address to a switch interface
            if link.get_dst_node().get_type() == 'lanswitch':
                #print('[DEBUG] node type is lanswitch')
                dst_interface = link.get_dst_node().create_interface([])
            else:
                dst_interface = link.get_dst_node().create_interface([
                    dst_if_ipv4_addr, dst_if_ipv6_addr])
            #print('[DEBUG] adding link_dst: (%s, %s)' % (link.get_dst_node().get_name(), dst_interface))
            link.set_dst(link.get_dst_node(), dst_interface)

        if dst_interface is None:
            dst_interface = link.get_dst_node().create_interface([])
            link.set_dst(link.get_dst_node(), dst_interface)

        self.__links__.append(link)
        #print('[TRACE] END OF add_link(link=%s)' % str(link))

    def get_link_count(self):
        return len(self.__links__)

    def get_links(self):
        return self.__links__

    def get_links_of_node(self, node):
        if node is None:
            raise ValueError('node cannot be None')

        return [link for link in self.__links__ if node in link.get_nodes()]

    def update(self, topology):
        #print('[DEBUG] updating topology with new values')
        self.__meta__.update(topology.__meta__)
        self.__nodes__.update(topology.__nodes__)
        self.__nodes_augmentations__.update(topology.__nodes_augmentations__)
        self.__bookkeeping__.update(topology.__bookkeeping__)
        for link in topology.get_links():
            if not link in self.__links__:
                self.add_link(link)

        #pp = pprint.PrettyPrinter(indent=4)
        #print('[DEBUG] topology contents:')
        #print('[DEBUG]  meta:')
        #pp.pprint(self.__meta__)

