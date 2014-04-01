#
# CORE
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# author: Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
'''
quagga.py: defines routing services provided by Quagga.
'''

import os

if os.uname()[0] == "Linux":
    from core.netns import nodes
elif os.uname()[0] == "FreeBSD":
    from core.bsd import nodes
from core.service import CoreService, addservice
from core.misc.ipaddr import IPPrefix, isIPAddress
from core.misc.ipaddr import IPv4Addr, IPv4Prefix, isIPv4Address
from core.misc.ipaddr import IPv6Addr, IPv6Prefix, isIPv6Address
from core.api import coreapi
from core.constants import *

from core.services import service_helpers
from core.services import service_flags

QUAGGA_USER="quagga"
QUAGGA_GROUP="quagga"
if os.uname()[0] == "FreeBSD":
    QUAGGA_GROUP="wheel"

class Zebra(CoreService):
    '''
    '''
    _name = "zebra"
    _group = "Quagga"
    _depends = ("vtysh", "LoopbackAddress")
    _dirs = ("/etc/quagga",  "/var/run/quagga")
    _configs = ("/etc/quagga/Quagga.conf",
                "quaggaboot.sh","/etc/quagga/vtysh.conf")
    _startindex = 35
    _startup = ("sh quaggaboot.sh zebra",)
    _shutdown = ("killall zebra", )
    _validate = ("pidof zebra", )

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Return the Quagga.conf or quaggaboot.sh file contents.
        '''
        if filename == cls._configs[0]:
            return cls.generateQuaggaConf(node, services)
        elif filename == cls._configs[1]:
            return cls.generateQuaggaBoot(node, services)
        elif filename == cls._configs[2]:
            return cls.generateVtyshConf(node, services)
        else:
            raise ValueError

    @classmethod
    def generateVtyshConf(cls, node, services):
        ''' Returns configuration file text.
        '''
        return "service integrated-vtysh-config"

    @classmethod
    def generateQuaggaConf(cls, node, services):
        ''' Returns configuration file text. Other services that depend on zebra
           will have generatequaggaifcconfig() and generatequaggaconfig()
           hooks that are invoked here.
        '''
        # we could verify here that filename == Quagga.conf
        cfg = ""
        for ifc in node.netifs():
            # do not ever include control interfaces in anything
            if hasattr(ifc, 'control') and ifc.control == True:
            #    cfg += "  "
            #    cfg += "\n  ".join(map(cls.addrstr, ifc.addrlist))
            #    cfg += "\n"
                continue

            cfg += "interface %s\n" % ifc.name

            cfgv4 = ""
            cfgv6 = ""
            want_ipv4 = False
            want_ipv6 = False
            for s in services:
                if cls._name not in s._depends:
                    continue
                ifccfg = s.generatequaggaifcconfig(node,  ifc)
                if s._ipv4_routing:
                    want_ipv4 = True
                if s._ipv6_routing:
                    want_ipv6 = True
                    cfgv6 += ifccfg
                else:
                    cfgv4 += ifccfg

            if want_ipv4:
                ipv4list = [x for x in ifc.addrlist if isIPv4Address(x.split('/')[0])]
                cfg += "  "
                cfg += "\n  ".join(map(cls.addrstr, ipv4list))
                cfg += "\n"
                cfg += cfgv4
            if want_ipv6:
                ipv6list = [x for x in ifc.addrlist if isIPv6Address(x.split('/')[0])]
                cfg += "  "
                cfg += "\n  ".join(map(cls.addrstr, ipv6list))
                cfg += "\n"
                cfg += cfgv6
            if not want_ipv4 and not want_ipv6:
                cfg += ifccfg
            cfg += "!\n"

        for s in services:
            if cls._name not in s._depends:
                continue
            cfg += s.generatequaggaconfig(node)
        return cfg

    @staticmethod
    def addrstr(x):
        ''' helper for mapping IP addresses to zebra config statements
        '''
        if x.find(".") >= 0:
            return "ip address %s" % x
        elif x.find(":") >= 0:
            return "ipv6 address %s" % x
        else:
            raise Value("invalid address: %s").with_traceback(x)

    @classmethod
    def generateQuaggaBoot(cls, node, services):
        ''' Generate a shell script used to boot the Quagga daemons.
        '''
        try:
            quagga_bin_search = node.session.cfg['quagga_bin_search']
            quagga_sbin_search = node.session.cfg['quagga_sbin_search']
        except KeyError:
            quagga_bin_search = '"/usr/local/bin /usr/bin /usr/lib/quagga"'
            quagga_sbin_search = '"/usr/local/sbin /usr/sbin /usr/lib/quagga"'
        return """\
#!/bin/sh
# auto-generated by zebra service (quagga.py)
QUAGGA_CONF=%s
QUAGGA_SBIN_SEARCH=%s
QUAGGA_BIN_SEARCH=%s
QUAGGA_STATE_DIR=%s
QUAGGA_USER=%s
QUAGGA_GROUP=%s

searchforprog()
{
    prog=$1
    searchpath=$@
    ret=
    for p in $searchpath; do
        if [ -x $p/$prog ]; then
            ret=$p
            break
        fi
    done
    echo $ret
}

waitforvtyfiles()
{
    for f in "$@"; do
        count=1
        until [ -e $QUAGGA_STATE_DIR/$f ]; do
            if [ $count -eq 10 ]; then
                echo "ERROR: vty file not found: $QUAGGA_STATE_DIR/$f" >&2
                return 1
            fi
            sleep 0.1
            count=$(($count + 1))
        done
    done
}

bootdaemon()
{
    QUAGGA_SBIN_DIR=$(searchforprog $1 $QUAGGA_SBIN_SEARCH)
    if [ "z$QUAGGA_SBIN_DIR" = "z" ]; then
        echo "ERROR: Quagga's '$1' daemon not found in search path:"
        echo "  $QUAGGA_SBIN_SEARCH"
        return 1
    fi

    if [ "$1" != "zebra" ]; then
        waitforvtyfiles zebra.vty
    fi

    $QUAGGA_SBIN_DIR/$1 -u $QUAGGA_USER -g $QUAGGA_GROUP -d
}

bootvtysh()
{
    QUAGGA_BIN_DIR=$(searchforprog $1 $QUAGGA_BIN_SEARCH)
    if [ "z$QUAGGA_BIN_DIR" = "z" ]; then
        echo "ERROR: Quagga's '$1' daemon not found in search path:"
        echo "  $QUAGGA_SBIN_SEARCH"
        return 1
    fi

    vtyfiles="zebra.vty"
    for r in rip ripng ospf6 ospf bgp babel; do
        if grep -q "^router \<${r}\>" $QUAGGA_CONF; then
            vtyfiles="$vtyfiles ${r}d.vty"
        fi
    done

    # wait for Quagga daemon vty files to appear before invoking vtysh
    waitforvtyfiles $vtyfiles

    $QUAGGA_BIN_DIR/vtysh -b
}

if [ "x$1" = "x" ]; then
    echo "ERROR: missing the name of the Quagga daemon to boot"
    exit 1
elif [ "$1" = "vtysh" ]; then
    bootvtysh $1
else
    bootdaemon $1
fi
""" % (cls._configs[0], quagga_sbin_search, quagga_bin_search, \
       QUAGGA_STATE_DIR, QUAGGA_USER, QUAGGA_GROUP)

addservice(Zebra)

class QuaggaService(CoreService):
    ''' Parent class for Quagga services. Defines properties and methods
        common to Quagga's routing daemons.
    '''
    _name = "QuaggaDaemon"
    _group = "Quagga"
    _depends = ("zebra", )
    _dirs = ()
    _configs = ()
    _startindex = 40
    _startup = ()
    _shutdown = ()
    _meta = "The config file for this service can be found in the Zebra service."

    _ipv4_routing = False
    _ipv6_routing = False

    @staticmethod
    def routerid(node):
        ''' Helper to return the first IPv4 address of a node as its router ID.
        '''
        return str(node.getLoopbackIPv4())

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
        return ""

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        return ""

    @classmethod
    def generatequaggaconfig(cls,  node):
        return ""

class Ospfv2(QuaggaService):
    ''' The OSPFv2 service provides IPv4 routing for wired networks. It does
        not build its own configuration file but has hooks for adding to the
        unified Quagga.conf file.
    '''
    _name = "OSPFv2"
    _startup = ("sh quaggaboot.sh ospfd",)
    _shutdown = ("killall ospfd", )
    _validate = ("pidof ospfd", )
    _ipv4_routing = True

    @staticmethod
    def mtucheck(ifc):
        ''' Helper to detect MTU mismatch and add the appropriate OSPF
        mtu-ignore command. This is needed when e.g. a node is linked via a
        GreTap device.
        '''
        if ifc.mtu != 1500:
            # a workaround for PhysicalNode GreTap, which has no knowledge of
            # the other nodes/nets
            return "  ip ospf mtu-ignore\n"
        if not ifc.net:
            return ""
        for i in ifc.net.netifs():
            if i.mtu != ifc.mtu:
                return "  ip ospf mtu-ignore\n"
        return ""

    @staticmethod
    def ptpcheck(ifc):
        ''' Helper to detect whether interface is connected to a notional
        point-to-point link.
        '''
        if isinstance(ifc.net, nodes.PtpNet):
            return "  ip ospf network point-to-point\n"
        return ""

    @classmethod
    def generatequaggaconfig(cls, node):
        cfg = "!\n! OSPFv2 (for IPv4) configuration\n!\n"
        cfg += "router ospf\n"
        cfg += "  router-id %s\n" % cls.routerid(node)
        cfg += "  redistribute connected\n"
        cfg += "  redistribute bgp\n"
        cfg += "!\n"

        return cfg

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        # do not include control interfaces
        if hasattr(ifc, 'control') and ifc.control == True:
            return ""

        cfg = cls.mtucheck(ifc)

        # find any link on which two equal netid's (i.e., AS numbers) are
        # present and configure an ospf-session on this interface
        # on all other interfaces, disable ospf
        for idx, net_netif in list(ifc.net._netif.items()):

            # skip our own interface
            if ifc == net_netif:
                continue

            # found the same AS, enable IGP/OSPF
            if node.netid == net_netif.node.netid:
                for a in ifc.addrlist:
                    if a.find(".") < 0:
                        continue
                    cfg += "  network %s area 0\n" % a
        cfg += "!\n"
        return cfg

addservice(Ospfv2)

class Ospfv3(QuaggaService):
    ''' The OSPFv3 service provides IPv6 routing for wired networks. It does
        not build its own configuration file but has hooks for adding to the
        unified Quagga.conf file.
    '''
    _name = "OSPFv3"
    _startup = ("sh quaggaboot.sh ospf6d",)
    _shutdown = ("killall ospf6d", )
    _validate = ("pidof ospf6d", )
    _ipv4_routing = True
    _ipv6_routing = True

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
            return "  ipv6 ospf6 ifmtu %d\n" % minmtu
        else:
            return ""

    @staticmethod
    def ptpcheck(ifc):
        ''' Helper to detect whether interface is connected to a notional
        point-to-point link.
        '''
        if isinstance(ifc.net, nodes.PtpNet):
            return "  ipv6 ospf6 network point-to-point\n"
        return ""

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg = "router ospf6\n"
        rtrid = cls.routerid(node)
        cfg += "  router-id %s\n" % rtrid
        cfg += "!\n"
        return cfg

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        if hasattr(ifc, 'control') and ifc.control == True:
            return ""

        cfg = cls.mtucheck(ifc)
        cfg += "  interface %s area 0.0.0.0\n" % ifc.name
        return cfg

addservice(Ospfv3)

class Ospfv3mdr(Ospfv3):
    ''' The OSPFv3 MANET Designated Router (MDR) service provides IPv6
        routing for wireless networks. It does not build its own
        configuration file but has hooks for adding to the
        unified Quagga.conf file.
    '''
    _name = "OSPFv3MDR"
    _ipv4_routing = True

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        cfg = cls.mtucheck(ifc)

        return cfg + """\
  ipv6 ospf6 instance-id 65
  ipv6 ospf6 hello-interval 2
  ipv6 ospf6 dead-interval 6
  ipv6 ospf6 retransmit-interval 5
  ipv6 ospf6 network manet-designated-router
  ipv6 ospf6 diffhellos
  ipv6 ospf6 adjacencyconnectivity uniconnected
  ipv6 ospf6 lsafullness mincostlsa
"""

addservice(Ospfv3mdr)

class Bgp(QuaggaService):
    '''' The BGP service provides interdomain routing.
        Peers must be manually configured, with a full mesh for those
        having the same AS number.
    '''
    _name = "BGP"
    _startup = ("sh quaggaboot.sh bgpd",)
    _shutdown = ("killall bgpd", )
    _validate = ("pidof bgpd", )
    _custom_needed = False
    _ipv4_routing = True
    _ipv6_routing = True

    @classmethod
    def generatequaggaconfig(cls, node):

        cfg = "!\n! BGP configuration\n!\n"
        cfg += "router bgp %s\n" % node.netid
        cfg += "  bgp router-id %s\n" % cls.routerid(node)
        cfg += "  redistribute connected\n"
        cfg += "  redistribute ospf\n"
        cfg += "  redistribute isis\n"

        cfg += "!\n"
        # aggregate networks that are being used for internal transit and access
        # TODO: find a more generic way. this approach works well for
        # two-AS-networks. ideally, each network should only aggregate the address
        # space that it allocates to it's client or the space that is being used by
        # it's internal routers (i.e., IGP, non-EGP)

        #cfg += "  aggregate-address 172.16.0.0 255.240.0.0 summary-only\n"
        #cfg += "  aggregate-address 192.168.0.0 255.255.0.0 summary-only\n"

        # don't aggregate networks that are being used for inter-AS routing
        #cfg += "  aggregate-address 10.0.0.0 255.0.0.0 summary-only\n!\n"
        #cfg += "!\n"

        # aggregate AS-local loopback addresses
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

            if hasattr(node, 'netid') and not node.netid is None:
                netid = node.netid
            else:
                netid = 0

            global_loopback_prefix = IPv4Prefix(global_loopback_prefix_str)

            baseprefix = IPv4Prefix('%s/%d' % (global_prefixbase, local_prefixlen))
            target_network_baseaddr = baseprefix.minaddr() + (netid * (baseprefix.numaddr() + 2))
            target_network_prefix = IPv4Prefix('%s/%d' % (target_network_baseaddr, local_prefixlen))
            cfg += "  aggregate-address %s %s summary-only\n" % (str(target_network_baseaddr), target_network_prefix.netmaskstr())
            cfg += "!\n"

        cfg += "!\n"


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
                if not node.netid == net_netif.node.netid:
                    if (hasattr(node, 'type') and node.type == "egp_node") and \
                            (hasattr(net_netif.node, 'type') and \
                            net_netif.node.type == "egp_node"):
                        for local_node_addr in localnetif.addrlist:
                            for remote_node_addr in net_netif.addrlist:
                                #local_node_addr = node.getLoopbackIPv4()
                                #remote_node_addr = net_netif.node.getLoopbackIPv4()
                                if (isIPv4Address(str(local_node_addr.split('/')[0])) and \
                                        isIPv4Address(str(remote_node_addr.split('/')[0]))) or \
                                        (isIPv6Address(str(local_node_addr.split('/')[0])) and \
                                        isIPv6Address(str(remote_node_addr.split('/')[0]))):
                                    cfg += "  neighbor %s remote-as %s\n" % \
                                            (str(remote_node_addr.split('/')[0]), str(net_netif.node.netid))
                                    cfg += "  neighbor %s update-source %s\n" % \
                                            (str(remote_node_addr.split('/')[0]),
                                                    str(local_node_addr.split('/')[0]))

        # configure IBGP connections
        confstr_list = [cfg]
        service_helpers.nodewalker(node, node, [], confstr_list,
                cls.nodewalker_callback)
        cfg = ''.join(confstr_list)

        cfg += "  address-family ipv6\n"
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
                if not node.netid == net_netif.node.netid:
                    if (hasattr(node, 'type') and node.type == "egp_node") and \
                            (hasattr(net_netif.node, 'type') and \
                            net_netif.node.type == "egp_node"):
                        for remote_node_addr in net_netif.addrlist:
                            if isIPv6Address(remote_node_addr.split('/')[0]):
                                cfg += "  neighbor %s activate\n" % \
                                        (str(remote_node_addr.split('/')[0]))
        # network fc00:3::/32
        # neighbor fc00::1:9 activate
        cfg += "  exit-address-family\n"

        cfg += "  ip forwarding\n"
        cfg += "  ipv6 forwarding\n"
        return cfg

    @staticmethod
    def nodewalker_callback(startnode, currentnode):
        result = []
        if service_flags.Router in startnode.services and \
                service_flags.Router in currentnode.services and \
                not startnode == currentnode and \
                startnode.netid == currentnode.netid:

            startnode_addr = startnode.getLoopbackIPv4()
            currentnode_addr = currentnode.getLoopbackIPv4()
            result = ["  neighbor %s remote-as %s\n" % \
                    (str(currentnode_addr), str(currentnode.netid)),
                    "  neighbor %s update-source %s\n" % \
                    (str(currentnode_addr), str(startnode_addr))
                    ]
            if service_flags.EGP in startnode.services:
                result.append("  neighbor %s next-hop-self\n" % str(currentnode_addr))
        return result

addservice(Bgp)

class Rip(QuaggaService):
    ''' The RIP service provides IPv4 routing for wired networks.
    '''
    _name = "RIP"
    _startup = ("sh quaggaboot.sh ripd",)
    _shutdown = ("killall ripd", )
    _validate = ("pidof ripd", )
    _ipv4_routing = True

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg = """\
router rip
  redistribute static
  redistribute connected
  redistribute ospf
  network 0.0.0.0/0
!
"""
        return cfg

addservice(Rip)

class Ripng(QuaggaService):
    ''' The RIP NG service provides IPv6 routing for wired networks.
    '''
    _name = "RIPNG"
    _startup = ("sh quaggaboot.sh ripngd",)
    _shutdown = ("killall ripngd", )
    _validate = ("pidof ripngd", )
    _ipv6_routing = True

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg = """\
router ripng
  redistribute static
  redistribute connected
  redistribute ospf6
  network ::/0
!
"""
        return cfg

addservice(Ripng)

class Babel(QuaggaService):
    ''' The Babel service provides a loop-avoiding distance-vector routing
    protocol for IPv6 and IPv4 with fast convergence properties.
    '''
    _name = "Babel"
    _startup = ("sh quaggaboot.sh babeld",)
    _shutdown = ("killall babeld", )
    _validate = ("pidof babeld", )
    _ipv6_routing = True

    @classmethod
    def generatequaggaconfig(cls,  node):
        cfg = "router babel\n"
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            cfg += "  network %s\n" % ifc.name
        cfg += "  redistribute static\n  redistribute connected\n"
        return cfg

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        type = "wired"
        if ifc.net and ifc.net.linktype == coreapi.CORE_LINK_WIRELESS:
            return "  babel wireless\n  no babel split-horizon\n"
        else:
            return "  babel wired\n  babel split-horizon\n"

addservice(Babel)

class ISIS(QuaggaService):
    ''' The user generated service isisd provides a ISIS!
    '''
    _name = "ISIS"
    _startup = ("sh quaggaboot.sh isisd",)
    _shutdown = ("killall isisd", )
    _validate = ("pidof isisd", )

    @classmethod
    def generatequaggaifcconfig(cls,  node,  ifc):
        added_ifc = False

        # do not include control interfaces
        if hasattr(ifc, 'control') and ifc.control == True:
            return ""

        cfg = ""

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

            # found the same AS, enable IGP/ISIS
            if not added_ifc and node.netid == net_netif.node.netid:
                cfg += "  ip router isis 1\n"
                cfg += "  ipv6 router isis 1\n"

                # other end of link is not router. don't send ISIS hellos
                if not service_flags.Router in net_netif.node.services:
                    cfg += "  isis passive\n"
                else:
                    cfg += "  isis circuit-type level-2-only\n"

                    # if this interface is connected via a point-to-point-link,
                    # set "isis network point-to-point.
                    # if this directive is not set, isis will speak mode lan
                    if isinstance(ifc.net, nodes.PtpNet):
                        cfg += "  isis network point-to-point\n"
                cfg += "!\n"

                # only add each interface once
                added_ifc = True

        return cfg


    @classmethod
    def generatequaggaconfig(cls, node):
        cfg = "!\n! ISIS configuration\n!\n"
        cfg += "log file /tmp/isis-%s.log debugging\n" % cls.routerid(node)
        cfg += "interface lo\n"
        cfg += " ip router isis 1\n"
        cfg += "!\n"

        cfg += "router isis 1\n"
        cfg += "  net %s\n" % cls.get_ISIS_ID(cls.routerid(node), str(node.netid))
        cfg += "!\n"

        return cfg

    @staticmethod
    def get_ISIS_ID(ipstr, netid):
        """ calculates and returns an ISIS-ID based on the supplied IP addr """
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
    _name = "vtysh"
    _group = "Quagga"
    _startindex = 45
    _startup = ("sh quaggaboot.sh vtysh",)
    _shutdown = ()
    _starttime = 5

    @classmethod
    def generateconfig(cls, node, filename, services):
        return ""

addservice(Vtysh)

