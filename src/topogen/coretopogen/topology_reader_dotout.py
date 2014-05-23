#
# topology_reader_dotout - reads a layouted ndoes list
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import subprocess

from coretopogen.topology_readwriter import TopologyReader
from coretopogen.topology_writer_dot import TopologyWriterDot

class TopologyReaderDotOut(TopologyReader):

    @staticmethod
    def add_nodemap_file(self, filename):
        pass

    @staticmethod
    def __read_nodefile__(filename):
        #print(('[DEBUG] reading "%s"' % filename))
        lines = []
        with open(filename, 'r') as fd:
            for line in fd.readlines():
                try:
                    name, x_pos, y_pos = line.split()
                    x_pos, y_pos = int(float(x_pos)), int(float(y_pos))
                except:
                    continue
                lines.append((name, x_pos, y_pos))
        return lines

    @staticmethod
    def read(filename=None, existing_topology=None):
        if existing_topology is None:
            raise ValueError('existing_topology is None')

        if filename is None:
            raise ValueError('filename is None')

        #print('[FOOO] writing DOT to "%s.dotout"' % filename)
        TopologyWriterDot.write('%s.dotout' % filename, existing_topology)
        lines = TopologyReaderDotOut.__read_nodefile__( \
                '%s.dotout.dotout' % filename)
        for hostname, x_pos, y_pos in lines:
            node = existing_topology.get_node(hostname)
            if x_pos < 50:
                x_pos += 50
            if y_pos < 50:
                y_pos += 50
            #print(('[TopologyReaderDotOut] node pos: (%s, %s) -> (%s, %s)' %
            #        (str(node.get_position()[0]), str(node.get_position()[1]),
            #        str(x_pos), str(y_pos))))
            node.set_position(x_pos, y_pos)

        return True, existing_topology
