#
# topology_reader_brite - classes for parsing topologies generated by BRITE
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

from core.constants import *

from coretopogen.nodes import *
from coretopogen.topology import Topology
from coretopogen.topology_readwriter import TopologyReader

class TopologyReaderBrite(TopologyReader):

    __topo_type__ = 'BRITE'
    __topology__ = None
    __nodemap__ = None

    def __init__(self):
        self.__topo_type__ = 'BRITE'
        self.__nodemap__ = None

    def add_nodemap_file(self, filename):
        __nodemap__ = KeyValueConf.parse(filename)
        self.__nodemap__ = {}
        for key, value in __nodemap__.items():
            tag = ''
            if key == 'AS_NODE':
                tag = 'egp'
            elif key == 'RT_NODE':
                tag = 'igp'
            elif key == 'RT_BORDER':
                tag = 'egp'
            self.__nodemap__[key] = {
                    'class': ASNode, 'model': value, 'tag': tag
                    }

    def __statemachine__(self, state=None, line=None):
        if state == 0:
            self.__topology__ = Topology()
            if not self.__nodemap__ is None:
                self.__topology__.set_nodemap(self.__nodemap__)
            #print('[DEBUG] Reading Metainfo...')
            state = 1

        if state == 1:
            if line.startswith('Topology:'):
                meta_nodes, meta_links = line[line.find('(')+1:line.rfind(')')].replace('Nodes','').replace('Edges', '').split(',')
                self.__topology__.add_meta('number_nodes', int(meta_nodes))
                self.__topology__.add_meta('number_links', int(meta_links))
            elif line.startswith('Model'):
                # TODO: implement model parsing
                #print('[DEBUG] found Model line: %s' % str(line))
                pass

            elif line.startswith('Nodes:'):
                #print(self.__topology__.__meta__)
                #print('[DEBUG] Reading Nodes...')
                state = 2

        elif state == 2:
            if line.startswith('Edges:'):
                #print('[DEBUG] Reading Edges...')
                state = 3
            # continue to read nodes
            else :
                node_id, x_pos, y_pos, in_degree, out_degree, as_id, node_model = line.split()

                node = None
                node_mapping = self.__topology__.get_node_mapping(node_model)
                if not node_mapping is None:
                    x_pos = int(float(x_pos))
                    y_pos = int(float(y_pos))
                    # if nodes are placed too close to the corners of the canvas, core is not
                    # able to auto-rearrange them anymore. if needed, move node to a safe
                    # position
                    if x_pos < 50:
                        x_pos += 50
                    if y_pos < 50:
                        y_pos += 50

                    #print('[DEBUG] node class: %s' % str(node_mapping['class']))
                    node = node_mapping['class']('n%d' % int(node_id))
                    # not neccessary if node-class sets correct model
                    node.set_model(node_mapping['model'])
                    node.set_tag(node_mapping['tag'])
                    #node.set_position(x_pos * 20, 3250 - (y_pos * 10))
                    node.set_position(x_pos * 20, (y_pos * 10))
                    # they start counting their ASes at 0. we start at 1
                    node.set_asn(int(as_id)+1)
                    # TODO: in_degree, out_degree are currently being ignored

                if not node is None:
                    self.__topology__.add_node(node.name, node)

        elif state == 3:

            line_list = line.split()
            edge_id, node_from, node_to, edge_length, delay, bandwidth, as_from, as_to=line.split()[:8]
            node_from = 'n%s' % node_from
            node_to = 'n%s' % node_to
            edge_type = line.split()[8:]

            link = PtpLink(self.__topology__.get_node(node_from), None,
                    self.__topology__.get_node(node_to), None, {
                    'edge_length': float(edge_length),
                    # BRITE: msec, CORE: microsec
                    'delay': int(float(delay) * 1000),
                    # BRITE: Mbps, CORE: bps
                    'bw': int(float(bandwidth) * 1000 * 1000),
                    'as_from': int(as_from),
                    'as_to': int(as_to),
                    'edge_type': edge_type
                    })

            self.__topology__.add_link(link)

        return state

    def read(self, filename=None, existing_topology=None):
        if filename is None:
            raise ValueError('filename cannot be None')

        #print('[DEBUG] type: %s' % str(self))
        f = self.__topo_type__
        #try:
        #print('[DEBUG] Parsing {filename} as {topo_type} file... '.format(
        #        filename=filename,
        #        topo_type=f),
        #        file=sys.stdout, flush=True)
        with open(filename, 'r') as f:
            state = 0
            for line in f:
                line = line.strip()
                if len(line) > 0:
                    #print('[DEBUG] parsing line: {line}'.format(line=line))
                    state = self.__statemachine__(state, line)
        #except Exception as e:
        #    print('Exception occured while reading topology: %s' % str(e))
        #    return False, None

        return True, self.__topology__

