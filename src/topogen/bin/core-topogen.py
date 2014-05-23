#!/usr/bin/env python3

#
# brite2core - an ad-hoc topology converter and enhancer from BRITE to CORE
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import datetime
import optparse
import os.path
import sys

from coretopogen.topology_generator import TopologyGenerator

if __name__ == "__main__" or __name__ == "__builtin__":

    def usage(err=0):
        """ print usage error and exit with given return code """
        parser.print_help()
        sys.exit(err)

    preamble = 'brite2core - a topology generation tool for CORE\n'
    usagestr = ('{0}%prog [-h|--help] [options] '
            '<in_file> <out_file>'.format(preamble))
    parser = optparse.OptionParser(usage=usagestr)
    parser.set_defaults()

    (opt, args) = parser.parse_args()

    if len(args) < 2:
        usage(1)

    infile = sys.argv[1]
    outfile = sys.argv[2]
    augmentfile = '/etc/core/brite.augment'
    brite_nodemapfile = '/etc/core/brite.nodemap'

    print(('infile: "%s", outfile: "%s"' % (infile, outfile)))

    topology_generator = TopologyGenerator()

    if not topology_generator.add_source_file(infile, 'brite'):
        usage(1)
    if not topology_generator.add_destination_file(outfile, 'imune'):
        usage(1)

    #topology_generator.add_destination_file(outfile, 'dot')
    #topology_generator.add_destination_file(outfile, 'edges')

    if os.path.exists(augmentfile):
        topology_generator.add_source_file(augmentfile, 'network_augmentation')

    if os.path.exists(brite_nodemapfile):
        topology_generator.add_nodemap_file(brite_nodemapfile, 'brite')

    topology_generator.add_source_file(infile, 'node_layout')

    # profiling foo..
    start = datetime.datetime.now()

    result = topology_generator.read_topology()
    if result:
        print('all specified input files were successfully parsed')
    else:
        print('some input files produced errors while being parsed')
        sys.exit(2)

    result = topology_generator.write_topology()
    if result:
        print('topology was successfully written to all specified output files')
    else:
        print('topology could not be written to all specified output formats')
        sys.exit(2)

    # profiling foo..
    print("elapsed time: %s" % str(datetime.datetime.now() - start))
    sys.exit(0)

###############################################################################

    """
    # generate a netflow9sink per AS
    as_nf_map = {}
    # TODO: randomize nodes list
    for node in nodes.values():
        if not node.as_number in as_nf_map and \
                node.nodetype == 'igp_node':
            as_nf_map[node.as_number] = node
    for node in as_nf_map.values():
        max_nodeid += 1
        snode = NF9SinkNode(str(max_nodeid))
        snode.set_position(node.x_pos + 50, node.y_pos + 50)
        snode.set_as_number(node.as_number)
        connection.register_node(snode)

        link = PtpLink(node, snode, {
                'edge_length': float(edge_length),
                # BRITE: msec, CORE: microsec
                'delay': int(float(0.1) * 1000),
                # BRITE: Mbps, CORE: bps
                'bw': int(float(10) * 1024 * 1024),
                'as_from': node.as_number,
                'as_to': snode.as_number,
                })

        link_node_cnt = 1
        prefix_len = 30

        if link_cnt % 255 == 0:
            snd_byte += 1

        print('address: 10.%d.%d.%d' % (snd_byte, link_cnt % 255, link_node_cnt))
        if link.src_interface is None:
            _, src_interface = link.src_node.add_interface(
                    "10.%d.%d.%d" % (snd_byte, link_cnt % 255, link_node_cnt),
                    prefix_len, pycore.nodes.VEth, connection.session)
            link.set_src_interface(src_interface)
        if link.dst_interface is None:
            _, dst_interface = link.dst_node.add_interface(
                    "10.%d.%d.%d" % (snd_byte, link_cnt % 255, link_node_cnt+1),
                    prefix_len, pycore.nodes.VEth, connection.session)
            link.set_dst_interface(dst_interface)

        connection.register_link(link)
        link_cnt += 1

###############################################################################

    # generate an access network or a content network per AS
    nodes_per_net = 5

    as_nf_map = {}
    # TODO: randomize nodes list
    nodeslist = list(nodes.values())
    nodeslist.reverse()
    for node in nodeslist:
        if not node.as_number in as_nf_map and \
                node.nodetype == 'igp_node':
            as_nf_map[node.as_number] = node
    for node in as_nf_map.values():
        # this is now our access router. create clients/hosts
        for i in range(nodes_per_net):
            max_nodeid += 1
            if node.as_number % 2 == 0:
                snode = ServerNode(str(max_nodeid))
            else:
                snode = ClientNode(str(max_nodeid))
            snode.set_position(node.x_pos + ((i+1)*50), node.y_pos + ((i+1)*50))
            snode.set_as_number(node.as_number)
            connection.register_node(snode)

            link = PtpLink(node, snode, {
                    'edge_length': float(edge_length),
                    # BRITE: msec, CORE: microsec
                    'delay': int(float(0.1) * 1000),
                    # BRITE: Mbps, CORE: bps
                    'bw': int(float(10) * 1024 * 1024),
                    'as_from': node.as_number,
                    'as_to': snode.as_number,
                    })

            link_node_cnt = 1
            prefix_len = 30

            if link_cnt % 255 == 0:
                snd_byte += 1

            print('address: 10.%d.%d.%d' % (snd_byte, link_cnt % 255, link_node_cnt))
            if link.src_interface is None:
                _, src_interface = link.src_node.add_interface(
                        "10.%d.%d.%d" % (snd_byte, link_cnt % 255, link_node_cnt),
                        prefix_len, pycore.nodes.VEth, connection.session)
                link.set_src_interface(src_interface)
            if link.dst_interface is None:
                _, dst_interface = link.dst_node.add_interface(
                        "10.%d.%d.%d" % (snd_byte, link_cnt % 255, link_node_cnt+1),
                        prefix_len, pycore.nodes.VEth, connection.session)
                link.set_dst_interface(dst_interface)

            connection.register_link(link)
            link_cnt += 1

###############################################################################

    connection.instantiate()
    connection.wait_for_instantiation()
    """
