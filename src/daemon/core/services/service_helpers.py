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

def nodewalker(startnode, currentnode, receiver_list,
        node_cb=None, visited_list=None, edge=None):
    """ implements a depth-first search starting at currentnode """

    if visited_list is None:
        visited_list = {'edges': [], 'nodes': []}

    visited_list['nodes'].append(currentnode)

    if not node_cb is None:
        receiver_list.extend(node_cb(startnode, currentnode))

    for localnetif in currentnode.netifs():
        if hasattr(localnetif, 'control'):
            continue

        for idx, net_netif in localnetif.net._netif.items():

            # skip our own interface
            if localnetif == net_netif:
                continue

            edge = ((currentnode.name, localnetif.name),
                    (net_netif.node.name, net_netif.name))
            if not edge in visited_list['edges']:

                if not net_netif.node in visited_list['nodes']:
                    visited_list['edges'].append(edge)
                    nodewalker(startnode, net_netif.node, receiver_list, node_cb,
                            visited_list, edge)
                else:
                    visited_list['edges'].append(edge)

