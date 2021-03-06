#
# CORE
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# author: Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

'''
quagga.py: defines routing services provided by Quagga.
'''

import os

if os.uname()[0] == 'Linux':
    from core.netns import nodes
elif os.uname()[0] == 'FreeBSD':
    from core.bsd import nodes
from core.service import CoreService, addservice
from core.misc.ipaddr import IPPrefix, isIPAddress
from core.misc.ipaddr import IPv4Addr, IPv4Prefix, isIPv4Address
from core.misc.ipaddr import IPv6Addr, IPv6Prefix, isIPv6Address
from core.misc.ipaddr import Loopback, Interface
from core.misc.netid import NetIDNodeMap
from core.api import coreapi
from core.constants import *

from core.services import service_helpers
from core.services import service_flags

QUAGGA_USER='quagga'
QUAGGA_GROUP='quagga'
if os.uname()[0] == 'FreeBSD':
    QUAGGA_GROUP='wheel'

class Zebra(CoreService):
    '''
    '''
    _name = 'zebra'
    _group = 'Quagga'
    _depends = ('vtysh',)
    _dirs = ('/etc/quagga',  '/var/run/quagga')
    _configs = ('/etc/quagga/daemons',
                '/etc/quagga/zebra.conf',
                '/etc/quagga/vtysh.conf')
    _startindex = 35
    _startup = ('/etc/init.d/quagga start',)
    _shutdown = ('/etc/init.d/quagga stop', )
    _validate = ('pidof zebra', )
    _starttime = 10

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Return the Quagga.conf or quaggaboot.sh file contents.
        '''
        if filename == cls._configs[0]:
            return cls.generateDaemonsConf(node, services)
        elif filename == cls._configs[1]:
            return cls.generateZebraConf(node, services)
        elif filename == cls._configs[2]:
            return cls.generateVtyshConf(node, services)
        else:
            raise ValueError

    @classmethod
    def generateVtyshConf(cls, node, services):
        ''' Returns configuration file text.
        '''
        return 'service integrated-vtysh-config'

    @classmethod
    def generateZebraConf(cls, node, services):
        ''' Returns configuration file text that defines which daemons to run.
        '''
        cfg = []

        cfg.append('log file /tmp/quagga-zebra-%s.log\n' % node.name)
        cfg.append('hostname %s\n' % node.name)
        cfg.append('agentx\n')
        cfg.append('interface lo\n')
        if node.enable_ipv4:
            cfg.append('  ip address %s/32\n' % node.getLoopbackIPv4())
        if node.enable_ipv6:
            cfg.append('  ipv6 address %s/128\n' % node.getLoopbackIPv6())

        for ifc in node.netifs():
            # do not ever include control interfaces in anything
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            cfg.append('interface %s\n' % ifc.name)
            for a in ifc.addrlist:
                if isIPv4Address(a):
                    cfg.append('  ip  address %s\n' % a)
                if isIPv6Address(a):
                    cfg.append('  ipv6  address %s\n' % a)
            cfg.append('!\n')

        if node.enable_ipv4:
            cfg.append('ip forwarding\n')
        if node.enable_ipv6:
            cfg.append('ipv6 forwarding\n')

        return ''.join(cfg)

    @classmethod
    def generateDaemonsConf(cls, node, services):
        ''' Returns configuration file text that defines which daemons to run.
        '''
        cfg = []
        cfg.extend([cls._name, '=yes\n'])
        for s in services:
            if cls._name not in s._depends:
                continue
            cfg.extend([s._daemonname, '=yes\n'])
        return ''.join(cfg)

addservice(Zebra)

class QuaggaService(CoreService):
    ''' Parent class for Quagga services. Defines properties and methods
        common to Quagga's routing daemons.
    '''
    _name = 'QuaggaDaemon'
    _daemonname = ''
    _group = 'Quagga'
    _depends = ('zebra', )
    _dirs = ()
    _configs = ()
    _startindex = 40
    _startup = ()
    _shutdown = ()
    _meta = 'The config file for this service can be found in the Zebra service.'

    _ipv4_routing = False
    _ipv6_routing = False

    @staticmethod
    def routerid(node):
        ''' Helper to return the first IPv4 address of a node as its router ID.
        '''
        # Use IPv4 loopback address of this node as the routerID.
        # Don't get v4-loopback-addr directly from node as the node might has
        # IPv4 disabled. Instead, directly query the central 'database' for the
        # IPv4 address that would be the nodes IPv4 loopback.
        return str(Loopback.getLoopbackIPv4(node))

    @staticmethod
    def rj45check(ifc):
        ''' Helper to detect whether interface is connected an external RJ45
        link.
        '''
        if ifc.net:
            for peerifc in ifc.net.netifs():
                if peerifc == ifc:
                    continue
                if isinstance(peerifc, nodes.RJ45Node):
                    return True
        return False

    @classmethod
    def generateconfig(cls,  node, filename, services):
        return cls.generatequaggaconfig(node)

    @classmethod
    def generatequaggaloconfig(cls, node):
        return ''

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        return ''

    @classmethod
    def generatequaggaconfig(cls,  node):
        return ''

    @classmethod
    def interface_iterator(cls, node, callback=None):
        result = []
        for ifc in node.netifs():
            # do not ever include control interfaces in anything
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            if not callback is None:
                result.extend(callback(node, ifc))
        return result

    @staticmethod
    def addrstr(x):
        ''' helper for mapping IP addresses to zebra config statements
        '''
        if isIPv4Address(x):
            return 'ip address %s' % x
        elif isIPv6Address(x):
            return 'ipv6 address %s' % x
        else:
            raise Value('invalid address: %s').with_traceback(x)


class Ospfv2(QuaggaService):
    ''' The OSPFv2 service provides IPv4 routing for wired networks. It does
        not build its own configuration file but has hooks for adding to the
        unified Quagga.conf file.
    '''
    _name = 'OSPFv2'
    _daemonname = 'ospfd'
    #_startup = ('sh quaggaboot.sh ospfd',)
    #_shutdown = ('killall ospfd', )
    _configs = ('/etc/quagga/ospfd.conf',)
    _validate = ('pidof ospfd', )
    _ipv4_routing = True
    #_starttime = 10

    @staticmethod
    def mtucheck(ifc):
        ''' Helper to detect MTU mismatch and add the appropriate OSPF
        mtu-ignore command. This is needed when e.g. a node is linked via a
        GreTap device.
        '''
        if ifc.mtu != 1500:
            # a workaround for PhysicalNode GreTap, which has no knowledge of
            # the other nodes/nets
            return '  ip ospf mtu-ignore\n'
        if not ifc.net:
            return ''
        for i in ifc.net.netifs():
            if i.mtu != ifc.mtu:
                return '  ip ospf mtu-ignore\n'
        return ''

    @staticmethod
    def ptpcheck(ifc):
        ''' Helper to detect whether interface is connected to a notional
        point-to-point link.
        '''
        #if isinstance(ifc.net, nodes.PtpNet):
        #    return '  ip ospf network point-to-point\n'
        return ''

    @classmethod
    def generate_network_statement(cls, node, ifc):
        cfg = []
        # find any link on which two equal netid's (i.e., AS numbers) are
        # present and configure an ospf-session on this interface
        # on all other interfaces, disable ospf
        for idx, net_netif in list(ifc.net._netif.items()):

            # skip our own interface
            if ifc == net_netif:
                continue
            # skip control interface
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            # found the same AS, enable IGP/OSPF
            if node.netid == net_netif.node.netid:
                if not service_flags.Router in net_netif.node.services:
                    cfg.append('  passive-interface %s\n' % ifc.name)
                for a in ifc.addrlist:
                    if not isIPv4Address(a):
                        continue
                    cfg.append('  network %s area 0.0.0.0\n' % a)
        return cfg

    @classmethod
    def generatequaggaconfig(cls, node):
        if not node.enable_ipv4:
            return ''

        cfg = ''

        cfg += cls.generatequaggaloconfig(node)

        for ifc in node.netifs():
            # do not ever include control interfaces in anything
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            cfg += 'interface %s\n' % ifc.name
            cfg += cls.generatequaggaifcconfig(node, ifc)
            ipv4list = [x for x in ifc.addrlist if isIPv4Address(x)]
            cfg += '  '
            cfg += '\n  '.join(map(cls.addrstr, ipv4list))
            cfg += '\n'
            cfg += '!\n'

        cfg = '!\n! OSPFv2 (for IPv4) configuration\n!\n'
        cfg += 'log file /tmp/quagga-ospf-%s.log\n' % node.name
        cfg += 'router ospf\n'
        cfg += '  router-id %s\n' % cls.routerid(node)
        cfg += '  redistribute connected\n'
        cfg += '!\n'
        cfg += ''.join(set(cls.interface_iterator(node,
                cls.generate_network_statement)))
        cfg += '!\n'
        return cfg

    @classmethod
    def generatequaggaloconfig(cls, node):
        if not node.enable_ipv4 and not node.enable_ipv6:
            return ''

        cfg = ''
        cfg += 'interface lo\n'
        cfg += '  ip address %s\n' % node.getLoopbackIPv4()
        cfg += '!\n'

        return cfg

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        if not node.enable_ipv4:
            return ''

        # do not include control interfaces
        if hasattr(ifc, 'control') and ifc.control == True:
            return ''

        cfg = ''
        cfg += cls.mtucheck(ifc)
        cfg += cls.ptpcheck(ifc)

        cfg += '!\n'
        return cfg

addservice(Ospfv2)

class Ospfv3(QuaggaService):
    ''' The OSPFv3 service provides IPv6 routing for wired networks. It does
        not build its own configuration file but has hooks for adding to the
        unified Quagga.conf file.
    '''
    _name = 'OSPFv3'
    _daemonname = 'ospf6d'
    #_startup = ('sh quaggaboot.sh ospf6d',)
    #_shutdown = ('killall ospf6d', )
    _configs = ('/etc/quagga/ospf6d.conf',)
    _validate = ('pidof ospf6d', )
    _ipv4_routing = True
    _ipv6_routing = True
    #_starttime = 10

    @staticmethod
    def minmtu(ifc):
        ''' Helper to discover the minimum MTU of interfaces linked with the
        given interface.
        '''
        mtu = ifc.mtu
        if not ifc.net:
            return mtu
        for i in ifc.net.netifs():
            if i.mtu < mtu:
                mtu = i.mtu
        return mtu

    @classmethod
    def mtucheck(cls, ifc):
        ''' Helper to detect MTU mismatch and add the appropriate OSPFv3
        ifmtu command. This is needed when e.g. a node is linked via a
        GreTap device.
        '''
        minmtu = cls.minmtu(ifc)
        if minmtu < ifc.mtu:
            return '  ipv6 ospf6 ifmtu %d\n' % minmtu
        else:
            return ''

    @classmethod
    def generate_area_statement(cls, node, ifc):
        cfg = []
        for idx, net_netif in list(ifc.net._netif.items()):

            # skip our own interface
            if ifc == net_netif:
                continue
            # skip control interface
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            # found the same AS, enable IGP/OSPF
            if node.netid == net_netif.node.netid:
                if service_flags.Router in net_netif.node.services:
                    cfg.append('  interface %s area 0.0.0.0\n' % ifc.name)

        return cfg

    @classmethod
    def generatequaggaconfig(cls,  node):
        if not node.enable_ipv6:
            return ''

        cfg = ''

        cfg += cls.generatequaggaloconfig(node)

        for ifc in node.netifs():
            # do not ever include control interfaces in anything
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            cfg += 'interface %s\n' % ifc.name
            cfg += cls.generatequaggaifcconfig(node, ifc)
            cfg += '!\n'

        cfg += 'log file /tmp/quagga-ospf6-%s.log\n' % node.name
        cfg += 'router ospf6\n'
        rtrid = cls.routerid(node)
        cfg += '  router-id %s\n' % rtrid
        cfg += '  redistribute connected\n'
        cfg += '!\n'
        cfg += ''.join(set(cls.interface_iterator(node,
                cls.generate_area_statement)))

        return cfg

    @classmethod
    def generatequaggaloconfig(cls, node):
        if not node.enable_ipv4 and not node.enable_ipv6:
            return ''

        cfg = ''

        return cfg

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        if not node.enable_ipv4 and not node.enable_ipv6:
            return ''

        if hasattr(ifc, 'control') and ifc.control == True:
            return ''

        enable_ifc = False
        for a in ifc.addrlist:
            if node.enable_ipv4 and isIPv4Address(a):
                enable_ifc = True
            if node.enable_ipv6 and isIPv6Address(a):
                enable_ifc = True

        cfg = ''
        if enable_ifc:
            cfg += cls.mtucheck(ifc)
            for idx, net_netif in list(ifc.net._netif.items()):

                # skip our own interface
                if ifc == net_netif:
                    continue
                # skip control interface
                if hasattr(ifc, 'control') and ifc.control == True:
                    continue

                # found the same AS, enable IGP/OSPF
                if node.netid == net_netif.node.netid:
                    if not service_flags.Router in net_netif.node.services:
                        # other end of link is not router. don't send hellos
                        cfg += '  ipv6 ospf6 passive\n'
                        break
        return cfg

addservice(Ospfv3)

class Ospfv3mdr(Ospfv3):
    ''' The OSPFv3 MANET Designated Router (MDR) service provides IPv6
        routing for wireless networks. It does not build its own
        configuration file but has hooks for adding to the
        unified Quagga.conf file.
    '''
    _name = 'OSPFv3MDR'
    _daemonname = 'ospf6d'
    _ipv4_routing = True
    #_starttime = 10

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        cfg = super().generatequaggaifcconfig(cls, node, ifc)

        # super() decides whether this interface is to be included.
        # honor its decision
        if len(cfg) == 0:
            return cfg

        return cfg + '''\
  ipv6 ospf6 instance-id 65
  ipv6 ospf6 hello-interval 2
  ipv6 ospf6 dead-interval 6
  ipv6 ospf6 retransmit-interval 5
  ipv6 ospf6 network manet-designated-router
  ipv6 ospf6 diffhellos
  ipv6 ospf6 adjacencyconnectivity uniconnected
  ipv6 ospf6 lsafullness mincostlsa
'''

addservice(Ospfv3mdr)

class Bgp(QuaggaService):
    '''' The BGP service provides interdomain routing.
        Peers must be manually configured, with a full mesh for those
        having the same AS number.
    '''
    _name = 'BGP'
    _daemonname = 'bgpd'
    #_startup = ('sh quaggaboot.sh bgpd',)
    #_shutdown = ('killall bgpd', )
    _configs = ('/etc/quagga/bgpd.conf',)
    _validate = ('pidof bgpd', )
    _custom_needed = False
    _ipv4_routing = True
    _ipv6_routing = True
    #_starttime = 20

    @classmethod
    def configure_EGP(cls, node):
        cfg = ''
        v6cfg = []
        # find any link on which two different netid's (i.e., AS numbers) are
        # present and configure a bgp-session between the two corresponding nodes.
        for localnetif in node.netifs():

            # do not include control interfaces
            if hasattr(localnetif, 'control') and localnetif.control == True:
                continue

            for idx, net_netif in list(localnetif.net._netif.items()):
                candidate_node = net_netif.node

                # skip our own interface
                if localnetif == net_netif.node:
                    continue

                # found two different ASes.
                if not node.netid == net_netif.node.netid and \
                        service_flags.EGP in net_netif.node.services:
                    for local_node_addr in localnetif.addrlist:

                        local_node_addr_str = str(local_node_addr.split('/')[0])
                        if not node.enable_ipv4 and \
                                isIPv4Address(local_node_addr):
                            continue
                        if not node.enable_ipv6 and \
                                isIPv6Address(local_node_addr):
                            continue

                        for remote_node_addr in net_netif.addrlist:
                            remote_node_addr_str = str(remote_node_addr.split('/')[0])
                            if not net_netif.node.enable_ipv4 and \
                                    isIPv4Address(remote_node_addr):
                                continue
                            if not net_netif.node.enable_ipv6 and \
                                    isIPv6Address(remote_node_addr):
                                continue

                            # for inter-AS links, use interface addresses
                            # instead of loopback addresses
                            if (isIPv4Address(local_node_addr) and \
                                    isIPv4Address(remote_node_addr)):
                                cfg += '  neighbor %s remote-as %s\n' % \
                                        (remote_node_addr_str, \
                                        str(net_netif.node.netid))

                            elif (isIPv6Address(local_node_addr) and \
                                    isIPv6Address(remote_node_addr)):
                                cfg += '  neighbor %s remote-as %s\n' % \
                                        (remote_node_addr_str, str(net_netif.node.netid))

                                v6cfg.append(('    neighbor %s activate\n' %
                                        remote_node_addr_str))
                                v6cfg.append(('    network %s\n' %
                                        str(local_node_addr)))

        return cfg, v6cfg


    @classmethod
    def generatequaggaconfig(cls, node):
        v6cfg = []
        v6prefixes = []

        if not node.enable_ipv4 and not node.enable_ipv6:
            return ''

        cfg = '!\n! BGP configuration\n!\n'
        cfg += 'log file /tmp/quagga-bgp-%s.log\n' % node.name
        cfg += 'router bgp %s\n' % node.netid
        cfg += '  bgp router-id %s\n' % cls.routerid(node)
        cfg += '  redistribute kernel\n'
        cfg += '  redistribute static\n'

        cfg += '!\n'

        if hasattr(node, 'netid') and not node.netid is None:
            netid = node.netid
        else:
            # TODO: netid 0 is invalid
            netid = 0

        # configure EBGP connections:
        if service_flags.EGP in node.services:
            tmpcfg, tmpv6cfg = cls.configure_EGP(node)
            cfg += tmpcfg
            v6cfg.extend(tmpv6cfg)

        # configure IBGP connections
        confstr_list = [cfg]
        # full mesh
        service_helpers.nodewalker(node, node, confstr_list,
                cls.nodewalker_ibgp_find_neighbors_callback)
        cfg = ''.join(confstr_list)

        if node.enable_ipv4 and service_flags.EGP in node.services:
            interface_net = Interface.getInterfaceNet_per_net(\
                    node.session.sessionid, netid, 4)
            loopback_net = Loopback.getLoopbackNet_per_net(\
                    node.session.sessionid, netid, 4)
            cfg += '  network %s\n' % str(loopback_net)
            cfg += '  network %s\n' % str(interface_net)
            cfg += '  aggregate-address %s summary-only\n' % str(loopback_net)
            cfg += '  aggregate-address %s summary-only\n' % str(interface_net)

        if node.enable_ipv6:
            v6_ibgp_neighbor_list = []
            service_helpers.nodewalker(node, node, v6_ibgp_neighbor_list,
                    cls.nodewalker_ibgp_find_neighbor_addrs_v6_callback)
            cfg += '  address-family ipv6\n'
            # activate IBGP neighbors
            cfg += ''.join([('    neighbor %s activate\n') % \
                    (str(remote_addr).split('/')[0]) \
                    for local_addr, remote_addr in v6_ibgp_neighbor_list])
            # activate EBGP neighbors
            cfg += ''.join(v6cfg)
            if service_flags.EGP in node.services:
                # announce networks
                interface_net = Interface.getInterfaceNet_per_net(\
                        node.session.sessionid, netid, 6)
                loopback_net = Loopback.getLoopbackNet_per_net(\
                        node.session.sessionid, netid, 6)
                cfg += '    network %s\n' % str(loopback_net)
                cfg += '    network %s\n' % str(interface_net)
                cfg += '    aggregate-address %s summary-only\n' % str(loopback_net)
                cfg += '    aggregate-address %s summary-only\n' % str(interface_net)
            adj_addrs = cls.collect_adjacent_loopback_addrs_v6(cls, node)
            for adj_addr in adj_addrs:
                cfg += '    network %s/128\n' % str(adj_addr)
            cfg += '\n  exit-address-family\n'

        return cfg

    @staticmethod
    def nodewalker_ibgp_find_neighbors_callback(startnode, currentnode):
        result = []
        if service_flags.Router in startnode.services and \
                service_flags.Router in currentnode.services and \
                not startnode == currentnode and \
                startnode.netid == currentnode.netid:

            startnode_ipversions = startnode.getIPversions()
            currentnode_ipversions = currentnode.getIPversions()
            ipversions = []
            for ipversion in 4, 6:
                if ipversion in startnode_ipversions and currentnode_ipversions:
                    ipversions.append(ipversion)

            for ipversion in ipversions:
                if ipversion == 4:
                    startnode_addr = startnode.getLoopbackIPv4()
                    currentnode_addr = currentnode.getLoopbackIPv4()
                elif ipversion == 6:
                    startnode_addr = startnode.getLoopbackIPv6()
                    currentnode_addr = currentnode.getLoopbackIPv6()

                result.extend(['  neighbor %s remote-as %s\n' % \
                        (str(currentnode_addr), str(currentnode.netid)),
                        '  neighbor %s update-source %s\n' % \
                        (str(currentnode_addr), str(startnode_addr))
                        ])

                if service_flags.EGP in startnode.services:
                    result.append('  neighbor %s next-hop-self\n' % str(currentnode_addr))
        return result

    @staticmethod
    def nodewalker_ibgp_find_neighbor_addrs_v6_callback(startnode, currentnode):
        result = []
        if service_flags.Router in startnode.services and \
                service_flags.Router in currentnode.services and \
                not startnode == currentnode and \
                startnode.netid == currentnode.netid:

            if startnode.enable_ipv6 and currentnode.enable_ipv6:
                result.append((startnode.getLoopbackIPv6(),
                        currentnode.getLoopbackIPv6()))

        return result

    @staticmethod
    def collect_adjacent_loopback_addrs_v6(cls, node):
        addrs = []
        for ifc in node.netifs():
            for idx, net_netif in list(ifc.net._netif.items()):

                # skip our own interface
                if ifc == net_netif:
                    continue
                # skip control interface
                if hasattr(ifc, 'control') and ifc.control == True:
                    continue

                # found the same AS, collect loopback addresses
                if node.netid == net_netif.node.netid:

                    # other end of link is no router. announce its loopback addr
                    if not service_flags.Router in net_netif.node.services:
                        if net_netif.node.enable_ipv6:
                            addrs.append(net_netif.node.getLoopbackIPv6())
        return addrs

addservice(Bgp)

class Rip(QuaggaService):
    ''' The RIP service provides IPv4 routing for wired networks.
    '''
    _name = 'RIP'
    _daemonname = 'ripd'
    #_startup = ('sh quaggaboot.sh ripd',)
    #_shutdown = ('killall ripd', )
    _configs = ('/etc/quagga/ripd.conf',)
    _validate = ('pidof ripd', )
    _ipv4_routing = True
    #_starttime = 10

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg = '''\
log file /tmp/quagga-ospf-%s.log
router rip
  redistribute static
  redistribute connected
  redistribute ospf
  network 0.0.0.0/0
!
''' % node.name
        return cfg

addservice(Rip)

class Ripng(QuaggaService):
    ''' The RIP NG service provides IPv6 routing for wired networks.
    '''
    _name = 'RIPNG'
    _daemonname = 'ripngd'
    #_startup = ('sh quaggaboot.sh ripngd',)
    #_shutdown = ('killall ripngd', )
    _configs = ('/etc/quagga/ripngd.conf',)
    _validate = ('pidof ripngd', )
    _ipv6_routing = True
    #_starttime = 10

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg = '''\
log file /tmp/quagga-ospf-%s.log
router ripng
  redistribute static
  redistribute connected
  redistribute ospf6
  network ::/0
!
''' % node.name
        return cfg

addservice(Ripng)

class Babel(QuaggaService):
    ''' The Babel service provides a loop-avoiding distance-vector routing
    protocol for IPv6 and IPv4 with fast convergence properties.
    '''
    _name = 'Babel'
    _daemonname = 'babeld'
    #_startup = ('sh quaggaboot.sh babeld',)
    #_shutdown = ('killall babeld', )
    _configs = ('/etc/quagga/babeld.conf',)
    _validate = ('pidof babeld', )
    _ipv6_routing = True
    #_starttime = 10

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg += 'log file /tmp/quagga-babel-%s.log\n' % node.name
        cfg = 'router babel\n'
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            cfg += '  network %s\n' % ifc.name
        cfg += '  redistribute static\n  redistribute connected\n'
        return cfg

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        type = 'wired'
        if ifc.net and ifc.net.linktype == coreapi.CORE_LINK_WIRELESS:
            return '  babel wireless\n  no babel split-horizon\n'
        else:
            return '  babel wired\n  babel split-horizon\n'

addservice(Babel)

class ISIS(QuaggaService):
    ''' The user generated service isisd provides a ISIS!
    '''
    _name = 'ISIS'
    _daemonname = 'isisd'
    #_startup = ('sh quaggaboot.sh isisd',)
    #_shutdown = ('killall isisd', )
    _configs = ('/etc/quagga/isisd.conf',)
    _validate = ('pidof isisd', )
    _ipv4_routing = True
    _ipv6_routing = True
    #_starttime = 10

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        added_ifc = False

        if not node.enable_ipv4 and not node.enable_ipv6:
            return ''

        # do not include control interfaces
        if hasattr(ifc, 'control') and ifc.control == True:
            return ''

        cfg = ''

        # find any link on which two equal netid's (e.g., AS numbers) are
        # present and on which two routers are present.
        # then configure an isis-session on this interface
        # on all other interfaces, disable isis
        for idx, net_netif in list(ifc.net._netif.items()):

            # only add each interface once
            if added_ifc:
                break

            # skip our own interface
            if ifc == net_netif:
                continue
            # skip control interface
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            # found the same AS, enable IGP/ISIS
            if not added_ifc:

                if node.enable_ipv4:
                    cfg += '  ip router isis 1\n'
                if node.enable_ipv6:
                    cfg += '  ipv6 router isis 1\n'

                if node.netid == net_netif.node.netid:
                    # other end of link is not router. don't send ISIS hellos
                    if not service_flags.Router in net_netif.node.services:
                        cfg += '  isis passive\n'
                    else:
                        cfg += '  isis circuit-type level-2-only\n'

                        # if this interface is connected via a point-to-point-link,
                        # set isis network point-to-point.
                        # if this directive is not set, isis will speak mode lan
                        if isinstance(ifc.net, nodes.PtpNet):
                            cfg += '  isis network point-to-point\n'
                elif service_flags.Router in net_netif.node.services:
                    cfg += '  isis passive\n'
                cfg += '!\n'

                # only add each interface once
                added_ifc = True

        return cfg

    @classmethod
    def generatequaggaloconfig(cls, node):
        if not node.enable_ipv4 and not node.enable_ipv6:
            return ''

        cfg = ''
        cfg += 'interface lo\n'
        if node.enable_ipv4:
            cfg += '  ip router isis 1\n'
        if node.enable_ipv6:
            cfg += '  ipv6 router isis 1\n'
        cfg += '  isis passive\n'
        cfg += '  isis metric 0\n'
        cfg += '!\n'

        return cfg

    @classmethod
    def generatequaggaconfig(cls, node):
        cfg = ''

        cfg += cls.generatequaggaloconfig(node)

        for ifc in node.netifs():
            # do not ever include control interfaces in anything
            if hasattr(ifc, 'control') and ifc.control == True:
                continue

            tmpcfg = 'interface %s\n' % ifc.name

            cfgv4 = ''
            cfgv6 = ''
            cfgvall = ''
            want_ipv4 = False
            want_ipv6 = False

            ifccfg = cls.generatequaggaifcconfig(node, ifc)
            if cls._ipv4_routing and node.enable_ipv4:
                want_ipv4 = True
            if cls._ipv6_routing and node.enable_ipv6:
                want_ipv6 = True

            if want_ipv4 and not want_ipv6:
                cfgv4 += ifccfg
            elif not want_ipv4 and want_ipv6:
                cfgv6 += ifccfg
            elif want_ipv4 and want_ipv6:
                cfgvall += ifccfg

            if want_ipv4 and not want_ipv6:
                ipv4list = [x for x in ifc.addrlist if isIPv4Address(x)]
                tmpcfg += cfgv4

            elif not want_ipv4 and want_ipv6:
                ipv6list = [x for x in ifc.addrlist if isIPv6Address(x)]
                tmpcfg += cfgv6

            elif want_ipv4 and want_ipv6:
                tmpcfg += cfgv4
                tmpcfg += cfgv6
                tmpcfg += cfgvall

            tmpcfg += '!\n'

            if want_ipv4 or want_ipv6:
                cfg += tmpcfg

        cfg += '! ISIS configuration\n'

        if node.enable_ipv4 or node.enable_ipv6:
            cfg += 'log file /tmp/quagga-isis-%s.log\n' % node.name
            cfg += 'router isis 1\n'
            cfg += '  net %s\n' % cls.get_ISIS_ID(cls.routerid(node), str(node.netid))
            cfg += '  metric-style wide\n'
            cfg += '!\n'

        return cfg

    @staticmethod
    def get_ISIS_ID(ipstr, netid):
        ''' calculates and returns an ISIS-ID based on the supplied IP addr '''
        # isis-is is 12 characters long
        # it has the format: 49.nnnn.aaaa.bbbb.cccc.00
        # where nnnn == netid (i.e., same on all routers)
        #       abc  == routerid (i.e., unique among all routers)

        #hexip = hex(int(IPv4Addr(ipstr).addr))[2:]
        #if len(hexip) < 8:
        #    hexip = '0%s' % hexip

        #netid = str(netid)
        #isisnetidlist = [ '0' for i in range(4 - len(netid)) ]
        #isisnetidlist.append(netid)
        #isisnetid = ''.join(isisnetidlist)

        # 49.1000.

        splitted = ''.join(['%03d' % int(e) for e in ipstr.split('.')])
        isisid = '49.1000.%s.%s.%s.00' % (splitted[:4], splitted[4:8], splitted[8:])
        print('[DEBUG] isis id: %s' % isisid)
        return isisid

addservice(ISIS)


class Vtysh(CoreService):
    ''' Simple service to run vtysh -b (boot) after all Quagga daemons have
        started.
    '''
    _name = 'vtysh'
    _group = 'Quagga'
    _startindex = 45
    #_startup = ('sh quaggaboot.sh vtysh',)
    _shutdown = ()
    #_starttime = 30
    _configs = ('/etc/quagga/vtysh.conf',)

    @classmethod
    def generateconfig(cls, node, filename, services):
        return ''

addservice(Vtysh)

