#
# topology_writer_dot - writes a list of edges of a topology
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

from coretopogen.topology_readwriter import TopologyWriter

class TopologyWriterEdges(TopologyWriter):

    @staticmethod
    def write(filename=None, topology=None):
        if topology is None:
            raise ValueError('topology is None')

        if filename is None:
            raise ValueError('filename is None')

        filename = '%s.edges' % filename

        with open(filename, 'w') as fd:
            for edge in topology.get_links():
                line = [edge.get_src_node().get_name(), ' ',
                        edge.get_dst_node().get_name(), '\n']
                fd.write(''.join(line))
        return True
