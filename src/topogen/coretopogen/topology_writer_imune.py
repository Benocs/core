#
# topology_writer_imune - writes a topology in IMUNE format
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

from coretopogen.topology_readwriter import TopologyWriter

class TopologyWriterImune(TopologyWriter):

    FILE_EXTENSION = 'imn'

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

    # key: topology key - value: imune key
    link_properties_map = {
            'bw': 'bandwidth',
            'delay': 'delay',
            }
    link_properties_factor_map = {
            'bw': 1,
            'delay': 1,
            }

    @staticmethod
    def __write_option_global__(fd, options=None):
        if options is None:
            options = TopologyWriterImune.default_options_global

        fd.write('option global {\n')
        for k, v in options.items():
            fd.write('\t%s %s\n' % (str(k), str(v)))
        fd.write('}\n\n')

    @staticmethod
    def __write_option_session__(fd, options=None):
        if options is None:
            options = TopologyWriterImune.default_options_session

        fd.write('option session {\n')
        for k, v in options.items():
            fd.write('\t%s=%s\n' % (str(k), str(v)))
        fd.write('}\n\n')

    @staticmethod
    def __write_canvas__(fd, canvas=None):
        if canvas is None:
            canvas = TopologyWriterImune.default_canvas

        fd.write('canvas c1 {\n')
        for k, v in canvas.items():
            fd.write('\t%s %s\n' % (str(k), str(v)))
        fd.write('}\n\n')

    @staticmethod
    def __write_links__(fd, links=None):
        if links is None:
            raise ValueError('refusing to write a topology without any links')

        if not isinstance(links, list):
            raise ValueError('links needs to be a list')

        if len(links) == 0:
            raise ValueError('refusing to write a topology without any links')

        link_count = 1
        for link in links:
            fd.write('link l%d {\n' % link_count)
            for k, v in link.properties.items():
                # do needed translations and only write known properties
                if k in TopologyWriterImune.link_properties_map:
                    k = TopologyWriterImune.link_properties_map[k]
                    if k in TopologyWriterImune.link_properties_factor_map:
                        v = v * TopologyWriterImune.link_properties_factor_map[k]
                    fd.write('\t%s %s\n' % (str(k), str(v)))
            nodeslist = [node[0].nodeid for node in link.nodes]
            fd.write('\tnodes {%s}\n' % ' '.join(nodeslist))
            fd.write('}\n\n')

            link_count += 1

    @staticmethod
    def __write_node_networkconfig__(fd, node, baseindentation=4):
        base_indentstr = '\t'

        #print('[DEBUG] __write_node_networkconfig__: %s' % str(node))

        fd.write('\tnetwork-config {\n')
        fd.write('\thostname %s\n' % (node.get_name()))
        fd.write('\t!\n')
        for intf in node.get_interfaces():
            fd.write('\tinterface %s\n' % (str(intf.get_name())))
            for ipv4_addr in intf.get_ipv4_addresses():
                fd.write('\t ip address %s/%s\n' % (str(ipv4_addr),
                        str(ipv4_addr.get_prefixlen())))
            for ipv6_addr in intf.get_ipv6_addresses():
                fd.write('\t ipv6 address %s/%s\n' % (str(ipv6_addr),
                        str(ipv6_addr.get_prefixlen())))
            fd.write('\t!\n')
        fd.write('\t}\n')

    @staticmethod
    def __write_node_links__(fd, localnode, global_links, baseindentation=4):
        base_indentstr = ''.join([' ' for i in range(baseindentation)])

        for link in global_links:
            # check whether this node is part of the link
            # if not, goto fail; err next link
            if not localnode in [linknode for linknode, linkinterface in link.nodes]:
                continue

            #print('[DEBUG] found node %s in link: %s' % (str(localnode.get_name()), str(link)))

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

                #print('[DEBUG] .. adding interface peer: {%s, %s} ==> {%s, %s}' %
                #        (localnode.get_name(), localinterface.get_name(),
                #        remotenode.get_name(), remoteinterface.get_name()))
                #print('[DEBUG] .. adding interface peer: {%s, %s} ==> {%s, %s}' %
                #        (localnode.nodeid, localinterface.get_name(),
                #        remotenode.nodeid, remoteinterface.get_name()))
                fd.write('%sinterface-peer {%s %s}\n' % (base_indentstr,
                        localinterface.get_name(), remotenode.nodeid))

    @staticmethod
    def __write_netid_subnet_map__(fd, topology=None):
        if topology is None:
            raise ValueError('refusing to write a topology without any topology')

        fd.write(topology.netid_subnet_map.get_map_string(-1))

    @staticmethod
    def __write_nodes__(fd, nodes=None, links=None):
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

        for node in nodes.values():
            fd.write('node %s {\n' % node.nodeid)
            if node.get_state():
                fd.write('\tstate on\n')
            else:
                fd.write('\tstate off\n')
            fd.write('\tnetid %d\n' % node.get_asn())
            fd.write('\ttype %s\n' % node.get_type())
            fd.write('\tmodel %s\n' % node.get_model())
            TopologyWriterImune.__write_node_networkconfig__(fd, node)
            fd.write('\tcanvas c1\n')

            node_pos = node.get_position()
            fd.write('\ticoncoords {%d.0 %d.0}\n' % (node_pos))

            # put the label 40px below the node
            label_pos = (node_pos[0], node_pos[1] + 40)
            fd.write('\tlabelcoords {%d.0 %d.0}\n' % (label_pos))
            TopologyWriterImune.__write_node_links__(fd, node, links)

            fd.write('}\n\n')

    @staticmethod
    def write(filename=None, topology=None):

        if topology is None:
            raise ValueError('topology is None')

        if filename is None:
            raise ValueError('filename is None')

        filename = '%s.%s' % (filename, TopologyWriterImune.FILE_EXTENSION)

        with open(filename, 'w') as fd:
            TopologyWriterImune.__write_netid_subnet_map__(fd, topology)
            TopologyWriterImune.__write_nodes__(fd, topology.get_nodes(),
                    topology.get_links())
            TopologyWriterImune.__write_links__(fd, topology.get_links())
            TopologyWriterImune.__write_canvas__(fd)
            TopologyWriterImune.__write_option_global__(fd)
            TopologyWriterImune.__write_option_session__(fd)
        return True
