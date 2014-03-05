# various CORE services that implement functions for routers
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

import os

from core.service import CoreService, addservice
from core.misc.ipaddr import IPv4Prefix, IPv6Prefix
from core.misc.utils import *

from core.services import utility

class LoopbackAddress(utility.UtilService):
    """ assigns a loopback ip address to each router """
    _name = "LoopbackAddress"
    _configs = ("loopback.sh",)
    _startup = ()
    _meta = "DEPRECATED. remove this service from your configuration"

    @classmethod
    def generateconfig(cls, node, filename, services):
        addr = node.getLoopbackIPv4()
        print(('[WARN] service LoopbackAddress is deprecated. Loopback address '
                'handling is now done directly by the node. This service does '
                'nothing and exists solely for backward compatibility.'))
        return ''

addservice(LoopbackAddress)

class InterASStaticRoute(utility.UtilService):
    """ set up a static route per external interface to point to loopback """
    _name = "InterASStaticRoute"
    _configs = ("interasstaticroute.sh",)
    _startup = ("sh interasstaticroute.sh",)
    _meta = "set up a static route per external interface to point to loopback"

    @classmethod
    def generateconfig(cls, node, filename, services):
        cfg = "#!/bin/sh\n"

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

                # found two different ASes
                if not node.netid == net_netif.node.netid:
                    if (hasattr(node, 'type') and node.type == "egp_node") and \
                            (hasattr(net_netif.node, 'type') and \
                            net_netif.node.type == "egp_node"):
                        remote_node_addr = net_netif.node.getLoopbackIPv4()
                        for addr in net_netif.addrlist:
                            addr = addr.split('/')[0]
                            cfg += "  ip route add %s/32 via %s\n" % (str(remote_node_addr), str(addr))

        return cfg

addservice(InterASStaticRoute)
