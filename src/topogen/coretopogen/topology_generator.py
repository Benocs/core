#
# topology_generator - classes for building network topologies
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import os

from coretopogen.topology import Topology
from coretopogen.topology_reader_augment import TopologyReaderAugment
from coretopogen.topology_reader_brite import TopologyReaderBrite
from coretopogen.topology_reader_dotout import TopologyReaderDotOut
from coretopogen.topology_writer_as_info import TopologyWriterASInfo
from coretopogen.topology_writer_dot import TopologyWriterDot
from coretopogen.topology_writer_edges import TopologyWriterEdges
from coretopogen.topology_writer_imune import TopologyWriterImune
from coretopogen.topology_writer_json import TopologyWriterJson

class TopologyGenerator():
    __in_fnames__ = None
    __out_fnames__ = None

    __topology__ = None

    def __init__(self):
        # xTODO: add support for multiple readers and multiple writers
        # xTODO: iterate over all readers, each one adds parts to the topology
        # TODO: find correct parser by analyzing header of input-file
        # xTODO: iterate over all writers, each one writes the complete topology into their resp. format

        self.__supported_input_types__ = {
                'brite': TopologyReaderBrite(),
                'node_layout': TopologyReaderDotOut(),
                'network_augmentation': TopologyReaderAugment(),
                }

        self.__supported_output_types__ = {
                'imune': TopologyWriterImune(),
                'json': TopologyWriterJson(),
                'dot': TopologyWriterDot(),
                'edges': TopologyWriterEdges(),
                'as_info': TopologyWriterASInfo(),
                }

        # {in,out}_fnames is a tuple of (filename, filetype) <string, string>
        self.__in_fnames__ = []
        self.__out_fnames__ = []

        self.__topology__ = Topology()

    def add_nodemap_file(self, filename, filetype=None):
        if filetype is None:
            raise NotImplementedError('automatic guessing of filetype is not yet supported')

        if not os.path.exists(filename):
            return False

        if not filetype.lower() in self.__supported_input_types__:
            return False

        self.__supported_input_types__[filetype].add_nodemap_file(filename)

    def add_source_file(self, filename, filetype=None):
        if filetype is None:
            raise NotImplementedError('automatic guessing of filetype is not yet supported')

        if not os.path.exists(filename):
            return False

        if not filetype.lower() in self.__supported_input_types__:
            return False

        self.__in_fnames__.append((filename, filetype))
        return True

    def add_destination_file(self, filename, filetype=None):
        if filetype is None:
            raise NotImplementedError('automatic guessing of filetype is not yet supported')

        if not filetype.lower() in self.__supported_output_types__:
            return False

        self.__out_fnames__.append((filename, filetype))
        return True

    def read_topology(self):
        """ returns True if all specified input files can be parsed as topologies,
            returns False if one or more of the specified input files cannot be parsed
        """
        global_result = True

        for fname, type in self.__in_fnames__:
            print(('[INFO] reading topology type: "%s"' % str(type)))
            (result, tmp_topo) = self.__supported_input_types__[type].read(fname, self.__topology__)
            if result:
                # add parsed topology information to global topology
                self.__topology__.update(tmp_topo)
            else:
                global_result = False

        return global_result

    def write_topology(self):
        """ returns True if all specified output files can be written to,
            returns False if the topology cannot be written to one or more
            of the specified output files
        """

        global_result = True
        for fname, type in self.__out_fnames__:
            result = self.__supported_output_types__[type].write(fname, self.__topology__)
            if not result:
                global_result = False

        return global_result

