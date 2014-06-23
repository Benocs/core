#
# topology_writer_as_info - writes a list of AS's and their nodes of a topology
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

from coretopogen.topology_readwriter import TopologyWriter

class TopologyWriterASInfo(TopologyWriter):

    @staticmethod
    def write(filename=None, topology=None):
        if topology is None:
            raise ValueError('topology is None')

        if filename is None:
            raise ValueError('filename is None')

        filename = '%s.as_info' % filename

        with open(filename, 'w') as fd:
            for node in topology.get_nodes().values():
                line = [node.get_name(), ' ', str(node.get_asn()), '\n']
                fd.write(''.join(line))
        return True
