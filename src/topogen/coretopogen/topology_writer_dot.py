#
# topology_writer_dot - writes a topology in DOT format
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import subprocess

from coretopogen.topology_readwriter import TopologyWriter
from coretopogen.topology_writer_as_info import TopologyWriterASInfo
from coretopogen.topology_writer_edges import TopologyWriterEdges

class TopologyWriterDot(TopologyWriter):

    @staticmethod
    def write(filename=None, topology=None):
        if topology is None:
            raise ValueError('topology is None')

        if filename is None:
            raise ValueError('filename is None')

        TopologyWriterEdges.write(filename, topology)
        TopologyWriterASInfo.write(filename, topology)
        #print('[BAAZZZ] calling core-topogen_node_pos.py %s' % filename)
        stdoutdata = subprocess.getoutput('%s %s %s' %
                ('core-topogen_node_pos.py', '%s' % filename, filename))
        return True
