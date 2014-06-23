#
# topology_readwriter - base classes for parsing and writing network topologies
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

class TopologyReader():

    def add_nodemap_file(self, filename):
        raise NotImplementedError

    def read(filename=None, existing_topology=None):
        raise NotImplementedError

class TopologyWriter():

    indentation = {
            'per_level': 4
            }

    @staticmethod
    def write(filename=None, topology=None):
        raise NotImplementedError

