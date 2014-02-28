# various helper foo (methods, classes) for CORE services
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

def nodewalker(startnode, currentnode, visited_list, receiver_list,
        node_cb = None):

    visited_list.append(currentnode)

    if not node_cb is None:
        receiver_list.extend(node_cb(startnode, currentnode))

    for localnetif in currentnode.netifs():
        for idx, net_netif in list(localnetif.net._netif.items()):
            # skip our own interface
            if localnetif == net_netif.node:
                continue

            if not net_netif.node in visited_list:
                nodewalker(startnode, net_netif.node,
                        visited_list, receiver_list, node_cb)

