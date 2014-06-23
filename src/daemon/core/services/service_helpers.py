# various helper foo (methods, classes) for CORE services
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

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

