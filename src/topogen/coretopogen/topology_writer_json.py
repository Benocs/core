#
# topology_writer_json - writes a topology in JSON format
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import json

from core.misc.netid import NetIDSubnetMap
from coretopogen.topology_readwriter import TopologyWriter

class TopologyWriterJson(TopologyWriter):

    FILE_EXTENSION = 'json'

    default_options_global = {
            # show interface names in core-gui
            'interface_names': 'no',
            # show ipv4 addresses in core-gui
            'ip_addresses': 'no',
            # show ipv6 addresses in core-gui
            'ipv6_addresses': 'no',
            # show node labels in core-gui
            'node_labels': 'no',
            # show link labels in core-gui
            'link_labels': 'no',
            # show api-messages in core-gui
            'show_api': 'no',
            # show background images in core-gui
            'background_images': 'no',
            # show annotations in core-gui
            'annotations': 'no',
            # show grid in core-gui
            'grid': 'no',
            # not used. we have our own traffic generators
            'traffic_start': 0,
            }

    default_options_session = {
            'controlnet': '192.168.128.0/17',
            'enablerj45': 1,
            'enablesdt': 0,
            'preservedir': 0,
            }

    default_canvas = {'name': '{Canvas1}'}

    # key: topology key - value: json key
    link_properties_map = {
            'bw': 'bandwidth',
            'delay': 'delay',
            }
    link_properties_factor_map = {
            'bw': 1,
            'delay': 1,
            }

    @staticmethod
    def __get_option_global__(options=None):
        if options is None:
            options = TopologyWriterJson.default_options_global

        cfg = {'option_global': {}}
        for k, v in options.items():
            cfg['option_global'][str(k)] = str(v)
        return cfg

    @staticmethod
    def __get_option_session__(options=None):
        if options is None:
            options = TopologyWriterJson.default_options_session

        cfg = {'option_session': {}}
        for k, v in options.items():
            cfg['option_session'][str(k)] = str(v)
        return cfg

    @staticmethod
    def __get_canvas__(canvas=None):
        if canvas is None:
            canvas = TopologyWriterJson.default_canvas

        cfg = {'c1': {}}
        for k, v in canvas.items():
            cfg['c1'][str(k)] = str(v)
        return cfg

    @staticmethod
    def __get_links__(links=None):
        if links is None:
            raise ValueError('refusing to write a topology without any links')

        if not isinstance(links, list):
            raise ValueError('links needs to be a list')

        if len(links) == 0:
            raise ValueError('refusing to write a topology without any links')

        cfgdict = {}
        link_count = 1
        for link in links:
            cfgdict[link_count] = {}
            for k, v in link.properties.items():
                # do needed translations and only write known properties
                if k in TopologyWriterJson.link_properties_map:
                    k = TopologyWriterJson.link_properties_map[k]
                    if k in TopologyWriterJson.link_properties_factor_map:
                        v = v * TopologyWriterJson.link_properties_factor_map[k]
                    cfgdict[link_count][str(k)] = str(v)
            cfgdict[link_count]['nodes'] = [node[0].nodeid for node in link.nodes]

            link_count += 1
        return cfgdict

    @staticmethod
    def __get_node_networkconfig__(node):
        cfgdict = {}

        cfgdict['hostname'] = node.get_name()
        cfgdict['interfaces'] = {}
        for intf in node.get_interfaces():
            cfgdict['interfaces'][intf.get_name()] = {}

            cfgdict['interfaces'][intf.get_name()]['ipv4'] = []
            for ipv4_addr in intf.get_ipv4_addresses():
                cfgdict['interfaces'][intf.get_name()]['ipv4'].append(
                        '%s/%s' % (str(ipv4_addr),
                        str(ipv4_addr.get_prefixlen())))

            cfgdict['interfaces'][intf.get_name()]['ipv6'] = []
            for ipv6_addr in intf.get_ipv6_addresses():
                cfgdict['interfaces'][intf.get_name()]['ipv6'].append(
                        '%s/%s' % (str(ipv6_addr),
                        str(ipv6_addr.get_prefixlen())))
        return cfgdict


    @staticmethod
    def __get_node_links__(localnode, global_links):

        cfglist = []

        for link in global_links:
            # check whether this node is part of the link
            # if not, goto fail; err next link
            if not localnode in [linknode for linknode, linkinterface in link.nodes]:
                continue

            # find local interface
            localinterface = None
            for linknode, linkinterface in link.nodes:
                if linknode == localnode:
                    localinterface = linkinterface
                    break

            if localinterface is None:
                raise ValueError(('something is seriously wrong. in this link, '
                        'i found our node but not our interface'))

            for remotenode, remoteinterface in link.nodes:
                # don't create a link to ourself
                if localnode == remotenode:
                    continue

                cfglist.append((localinterface.get_name(), remotenode.nodeid))
        return cfglist

    @staticmethod
    def __get_netid_subnet_map__(topology=None):
        if topology is None:
            raise ValueError('refusing to write a topology without any topology')

        sessionid = -1

        if not sessionid in NetIDSubnetMap.__mapping__:
            raise ValueError(('sessionid: "%s" not found in NetIDSubnetMap' %
                    str(sessionid)))

        subnetmap = {}
        for ipfam in 4, 6:
            subnetmap[ipfam] = []

            for subnet, netid in NetIDSubnetMap.__mapping__[sessionid][ipfam].items():
                subnetmap[ipfam].append((netid, subnet))

        return subnetmap

    @staticmethod
    def __get_nodes__(nodes=None, links=None):
        if nodes is None:
            raise ValueError('refusing to write a topology without any nodes')
        if not isinstance(nodes, dict):
            raise ValueError('nodes needs to be a dict')
        if len(nodes) == 0:
            raise ValueError('refusing to write a topology without any nodes')
        if links is None:
            raise ValueError('refusing to write a topology without any links')
        if not isinstance(links, list):
            raise ValueError('links needs to be a list')
        if len(links) == 0:
            raise ValueError('refusing to write a topology without any links')

        nodesdict = {}

        for node in nodes.values():
            nodesdict[node.nodeid] = {}
            if node.get_state():
                nodesdict[node.nodeid]['state'] = 'on'
            else:
                nodesdict[node.nodeid]['state'] = 'off'
            nodesdict[node.nodeid]['network_cfg'] = TopologyWriterJson.__get_node_networkconfig__(node)
            nodesdict[node.nodeid]['netid'] = node.get_asn()
            nodesdict[node.nodeid]['type'] = node.get_type()
            nodesdict[node.nodeid]['model'] = node.get_model()
            nodesdict[node.nodeid]['canvas'] = 'canvas c1'
            node_pos = node.get_position()
            nodesdict[node.nodeid]['pos'] = '%d.0 %d.0' % node_pos
            # put the label 40px below the node
            nodesdict[node.nodeid]['label_pos'] = '%d.0 %d.0' % (node_pos[0], node_pos[1] + 40)
            nodesdict[node.nodeid]['links'] = TopologyWriterJson.__get_node_links__(node, links)

        return nodesdict

    @staticmethod
    def write(filename=None, topology=None):

        if topology is None:
            raise ValueError('topology is None')

        if filename is None:
            raise ValueError('filename is None')

        filename = '%s.%s' % (filename, TopologyWriterJson.FILE_EXTENSION)

        topologydict = {}

        with open(filename, 'w') as fd:
            topologydict['netid_subnet_map'] = TopologyWriterJson.__get_netid_subnet_map__(topology)
            topologydict['nodes'] = TopologyWriterJson.__get_nodes__(topology.get_nodes(),
                    topology.get_links())
            topologydict['links'] = TopologyWriterJson.__get_links__(topology.get_links())
            topologydict['canvas'] = TopologyWriterJson.__get_canvas__()
            topologydict['global'] = TopologyWriterJson.__get_option_global__()
            topologydict['session'] = TopologyWriterJson.__get_option_session__()

            fd.write(json.dumps(topologydict, sort_keys=True, indent=4))
        return True
