#
# topology_reader_augment - classes that augment a given topology with new nodes
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import math
import pprint
import random
import sys

from core.constants import *

from coretopogen.nodes import *
from coretopogen.topology import Topology
from coretopogen.topology_readwriter import TopologyReader

class TopologyReaderAugment(TopologyReader):

    __topo_type__ = 'AUGMENT'
    __topology__ = None

    __bookkeeping__ = None


    __comment_delimenter__ = '#'
    __type_value_delimenter__ = '='

    def __init__(self):
        self.__topo_type__ = 'AUGMENT'
        self.__topology__ = Topology()
        self.__bookkeeping__ = {
                'switch_nodes_deployed': 0,
                # key: cls_name, value: max_id (== number of deployed nodes)
                'augmentations_deployed': {}
                }

    def read(self, filename=None, existing_topology=None):
        if not existing_topology is None:
            self.__topology__.update(existing_topology)

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
                    state = self.statemachine(state, line)
        state = 2
        state = self.statemachine(state)
        #except Exception as e:
        #    print('Exception occured while reading topology: %s' % str(e))
        #    return False, None

        return True, self.__topology__

    def statemachine(self, state=None, line=None):
        #pp = pprint.PrettyPrinter(indent=4)
        #print('[DEBUG] state: %s' % str(state))
        if state == 0:
            #print('[DEBUG] Reading Metainfo...')
            state = 1

        # parse file
        if state == 1:
            line_list = [lineelement.strip() for lineelement in \
                    line.split(TopologyReaderAugment.__type_value_delimenter__)]
            #print('[DEBUG] line_list: %s' % str(line_list))

            if line.startswith(TopologyReaderAugment.__comment_delimenter__):
                pass

            elif line_list[0] == 'augmentation_types':
                augmentation_types = [augmentation_type.strip() \
                        for augmentation_type in line_list[1].split(',')]
                #print('[DEBUG] augmentation types: %s' % str(augmentation_types))
                self.__topology__.add_meta('augmentation_types',
                        augmentation_types)

            elif line_list[0] == 'one_of':
                one_of_list = [one_of_element.strip() \
                        for one_of_element in line_list[1].split(',')]
                #print('[DEBUG] per AS, create only one of: %s' % str(one_of_list))
                self.__topology__.add_meta('one_of',
                        one_of_list)

            elif line_list[0] == 'any_of':
                any_of_list = [any_of_element.strip() \
                        for any_of_element in line_list[1].split(',')]
                #print('[DEBUG] per AS, create any combination of: %s' % str(any_of_list))
                self.__topology__.add_meta('any_of',
                        any_of_list)

            else:
                for aug_type in self.__topology__.get_meta('augmentation_types'):
                    if line_list[0] == '%s_class' % aug_type:
                        self.__topology__.add_meta(
                                '%s_class' % aug_type,
                                line_list[1])
                    elif line_list[0] == 'min_%s_networks_global' % aug_type:
                        self.__topology__.add_meta(
                                'min_%s_networks_global' % aug_type,
                                int(line_list[1]))
                    elif line_list[0] == 'max_%s_networks_global' % aug_type:
                        self.__topology__.add_meta(
                                'max_%s_networks_global' % aug_type,
                                int(line_list[1]))
                    elif line_list[0] == 'min_%s_networks_per_as' % aug_type:
                        self.__topology__.add_meta(
                                'min_%s_networks_per_as' % aug_type,
                                int(line_list[1]))
                    elif line_list[0] == 'max_%s_networks_per_as' % aug_type:
                        self.__topology__.add_meta(
                                'max_%s_networks_per_as' % aug_type,
                                int(line_list[1]))
                    elif line_list[0] == 'create_%s_networks_probability' % aug_type:
                        self.__topology__.add_meta(
                                'create_%s_networks_probability' % aug_type,
                                float(line_list[1]))
                    elif line_list[0] == 'min_nodes_per_%s_network' % aug_type:
                        self.__topology__.add_meta(
                                'min_nodes_per_%s_network' % aug_type,
                                int(line_list[1]))
                    elif line_list[0] == 'max_nodes_per_%s_network' % aug_type:
                        self.__topology__.add_meta(
                                'max_nodes_per_%s_network' % aug_type,
                                int(line_list[1]))

        # assemble meta variables
        elif state == 2:
            augtypes = self.__topology__.get_meta('augmentation_types')
            if not augtypes is None and isinstance(augtypes, list):
                for augtype in augtypes:
                    #print('[DEBUG] handling augmentation type: %s' % augtype)
                    meta_keys = [
                            '%s_class' % augtype,
                            'min_%s_networks_per_as' % augtype,
                            'max_%s_networks_per_as' % augtype,
                            'create_%s_networks_probability' % augtype,
                            'min_nodes_per_%s_network' % augtype,
                            'max_nodes_per_%s_network' % augtype,
                            ]
                    #optional_meta_keys = [
                    #        'min_%s_networks_global' % augtype,
                    #        'max_%s_networks_global' % augtype,
                    #        ]
                    for meta_key in meta_keys:
                        if self.__topology__.get_meta(meta_key) is None:
                            raise ValueError(('Augmentation Type: "%s" is not '
                                'correctly specified. At least, the key "%s" '
                                'is missing. Bailing out' % (str(augtype),
                                    str(meta_key))))

                    # initialize book keeping
                    self.__bookkeeping__['augmentations_deployed'][augtype] = 0

            state = 3

            #print('[DEBUG] meta contents:')
            #pp.pprint(self.__topology__.__meta__)

        # fall through (from state 2); create augmentations
        if state == 3:

            global_augmentation_result = False
            augmentation_trial = 0
            max_augmentation_trials = 10

            backup_topology = Topology()
            backup_topology.update(self.__topology__)

            # sometime the dice are not in our favor. retry sometimes in case we didn't reach our
            # goal
            while not global_augmentation_result and augmentation_trial < max_augmentation_trials:
                round_augmentation_result = True

                # get me a fresh topology
                if augmentation_trial > 0:
                    print(('[INFO] could not apply all augmentation types. retrying with a fresh '
                            'topology %d/%d' % (augmentation_trial, max_augmentation_trials)))
                    self.__topology__ = Topology()
                    self.__topology__.update(backup_topology)
                    self.__bookkeeping__ = {
                            'switch_nodes_deployed': 0,
                            # key: cls_name, value: max_id (== number of deployed nodes)
                            'augmentations_deployed': {}
                            }
                    for augtype in self.__topology__.get_meta('augmentation_types'):
                        self.__bookkeeping__['augmentations_deployed'][augtype] = 0

                # create list of all assigned asn's
                asn_list = list(dict.fromkeys([node.get_asn() for node in
                    self.__topology__.get_nodes().values()]))
                #print('[DEBUG] asn list: ')
                #pp.pprint(asn_list)


                #print('[DEBUG] augtypes: %s' % str(self.__topology__.get_meta('augmentation_types')))
                for augtype in self.__topology__.get_meta('augmentation_types'):
                    print('[DEBUG] augmentation type: %s' % augtype)
                    # key: ASN, value: count of networks of augtype in that AS
                    self.__bookkeeping__['%s_networks_per_as' % augtype] = {}
                    # key: ASN, value: count of nodes of augtype in that AS
                    self.__bookkeeping__['nodes_per_%s_network' % augtype] = {}
                    self.__bookkeeping__['max_node_id_for_%s_network' % augtype] = 0

                    for asn in asn_list:
                        self.__bookkeeping__['%s_networks_per_as' % augtype][asn] = 0

                    #pp.pprint(self.__bookkeeping__['%s_networks_per_as' % augtype])

                    # loop until we assigned at least min_AUGTYPE_networks_per_as
                    # but not more than max_AUGTYPE_networks_per_as
                    max_loop = 10
                    loop_cnt = 0

                    # loop while:
                    # * each AS has at least min_AUGTYPE_networks_per_as deployed
                    # and
                    # * at least min_AUGTYPE_networks_global are deployed (if specified)
                    continue_to_loop = True
                    while continue_to_loop:

                        # if we solve our minimum per AS requirements, flag exit..
                        if min(self.__bookkeeping__['%s_networks_per_as' % augtype].values()) >= \
                                self.__topology__.get_meta('min_%s_networks_per_as' % augtype):
                            continue_to_loop = False

                        # ..but if the global requirements are not yet met, continue..
                        min_networks_global = self.__topology__.get_meta('min_%s_networks_global' % augtype)
                        deployed_networks_global = self.__bookkeeping__['augmentations_deployed'][augtype]
                        if not min_networks_global is None and \
                                deployed_networks_global < min_networks_global:
                            continue_to_loop = True

                        # ..except we reached our maximum loop count
                        if loop_cnt >= max_loop:
                            continue_to_loop = False

                        # assemble and randomize list of potential nodes
                        nodes_list = list(self.__topology__.get_nodes().values())
                        #nodes_list = self.__topology__.get_non_augmented_nodes()
                        random.shuffle(nodes_list)
                        #print('[DEBUG] nodes_list: %d' % len(nodes_list))
                        #pp.pprint(nodes_list)

                        for node in nodes_list:
                            # we only augment igp_nodes
                            if not node.get_tag() == 'igp':
                                #print(('[DEBUG] skipping non-core router: %s' % node.get_name()))
                                continue

                            asn = node.get_asn()

                            # created enough networks of this augmentation type.
                            # skip
                            if not self.__topology__.get_meta('max_%s_networks_global' % augtype) is None and \
                                    self.__bookkeeping__['augmentations_deployed'][augtype] >= \
                                    self.__topology__.get_meta('max_%s_networks_global' % augtype):
                                #print(('[DEBUG] skiping node of AS %d as '
                                #        'enough %s are deployed in this AS' % \
                                #        (asn, augtype)))
                                continue
                            #else:
                            #    print(('[DEBUG] handling node: %s' % node.get_name()))

                            if not asn in self.__bookkeeping__['%s_networks_per_as' % augtype]:
                                self.__bookkeeping__['%s_networks_per_as' % augtype][asn] = 0

                            if self.__bookkeeping__['%s_networks_per_as' % augtype][asn] < \
                                    self.__topology__.get_meta('max_%s_networks_per_as' % augtype):

                                #print(('[DEBUG] %s_networks in this as(%s): %s of min: %s, max: %s' %
                                #    (augtype, str(asn), str(self.__bookkeeping__['%s_networks_per_as' % augtype][asn]),
                                #    str(self.__topology__.get_meta('min_%s_networks_per_as' % augtype)),
                                #    str(self.__topology__.get_meta('max_%s_networks_per_as' %
                                #            augtype)))))

                                # throw some dice
                                if random.random() <= \
                                        self.__topology__.get_meta('create_%s_networks_probability' % augtype):
                                    n_nodes = random.randint(
                                            self.__topology__.get_meta('min_nodes_per_%s_network' %
                                                augtype),
                                            self.__topology__.get_meta('max_nodes_per_%s_network' %
                                                augtype))
                                    #print(('[DEBUG] dice say that we create a new '
                                    #        '%s_network with %s nodes here: %s') %
                                    #        (augtype, str(n_nodes), str(node.get_name())))
                                    self.__bookkeeping__['%s_networks_per_as' % augtype][asn] += 1

                                    # class to create new nodes from, number of nodes to create, router
                                    # to connect to
                                    self.create_augmentation(augtype, n_nodes, node)
                                    self.__topology__.add_augmented_node(node, augtype)
                        loop_cnt += 1

                    # sanitation checks follow
                    if max_loop == loop_cnt:
                        round_augmentation_result = False
                        print(('[WARNING] I reached the maximum number of loops '
                            'for augmentation type "%s". In the worst case, I '
                            'deployed only "%d" entities in that AS but the '
                            'requirement states that at least "%d" per AS have to '
                            'be deployed. I\'m sorry') % (augtype,
                                min(self.__bookkeeping__['%s_networks_per_as' % augtype].values()),
                                self.__topology__.get_meta('min_%s_networks_per_as' % augtype)))
                    elif not self.__topology__.get_meta('min_%s_networks_global' % augtype) is None and \
                            self.__bookkeeping__['augmentations_deployed'][augtype] < \
                            self.__topology__.get_meta('min_%s_networks_global' % augtype):
                        round_augmentation_result = False
                        print(('[INFO] did not deploy enough %s networks '
                                '(%d of at least %d). I will retry next '
                                'round..' % (augtype,
                                self.__bookkeeping__['augmentations_deployed'][augtype],
                                self.__topology__.get_meta('min_%s_networks_global' % augtype))))
                    else:
                        print('[INFO] augmentation type "%s" successfully applied' % augtype)
                    #pp.pprint(self.__bookkeeping__['%s_networks_per_as' % augtype])

                if round_augmentation_result:
                    global_augmentation_result = True
                augmentation_trial += 1

            if augmentation_trial == max_augmentation_trials:
                print(('[ERROR] could not apply all augmentation types. even '
                        'after several trials. You might want to change your '
                        'parameters. Bailing out and returning what I could '
                        'augment'))
            elif global_augmentation_result:
                print('[INFO] augmentation successfully done')

            state = 4

        return state

    def create_augmentation(self, augtype, n_nodes, src_node):
        #print('[DEBUG] create_augmentation(augtype: %s, n_nodes: %d, src_node: %s)' % \
        #        (augtype, n_nodes, str(src_node)))

        # do some book keeping - count deployed networks
        if not augtype in self.__bookkeeping__['augmentations_deployed']:
            self.__bookkeeping__['augmentations_deployed'][augtype] = 0
        self.__bookkeeping__['augmentations_deployed'][augtype] += 1

        node = None
        cls_name = self.__topology__.get_meta('%s_class' % augtype)
        #print('[DEBUG] node class: %s' % cls_name)

        ptp = True
        if n_nodes > 1:
            ptp = False

        # we need a switch for non-point-to-point-links
        if not ptp:
            switch_id = self.__bookkeeping__['switch_nodes_deployed']
            self.__bookkeeping__['switch_nodes_deployed'] += 1

            # add switch node here
            switch = SwitchNode('switch%s' % str(switch_id))
            x_pos = src_node.x_pos + 50
            y_pos = src_node.y_pos + 50
            switch.set_position(x_pos, y_pos)
            switch.set_asn(src_node.get_asn())
            #print('[DEBUG] adding switch: %s' % str(switch))
            self.__topology__.add_node(switch.name, switch)

            # link between router and switch
            link = PtpLink(src_node, None, switch, None, {
                # TODO: how to allocate bandwidth
                # CORE: microsec
                'delay': 10,
                # TODO: how to allocate delay
                # CORE: bps
                'bw': 10000000,
                })
            self.__topology__.add_link(link)


        for i in range(n_nodes):
            # do some book keeping - count deployed nodes
            if not cls_name in self.__bookkeeping__['augmentations_deployed']:
                self.__bookkeeping__['augmentations_deployed'][cls_name] = 0

            idx = self.__bookkeeping__['augmentations_deployed'][cls_name]
            self.__bookkeeping__['augmentations_deployed'][cls_name] += 1
            try:
                node = eval('%s("%s%d")' % (cls_name, cls_name, idx))
            except NameError:
                raise NameError('class "%s" for augtype: %s not found' % \
                        (cls_name, augtype))

            x_pos = src_node.x_pos + 100 + (200 * (math.cos(i)) + \
                    random.randint(0, 200))
            y_pos = src_node.y_pos + 100 + (200 * (math.sin(i)) + \
                    random.randint(0, 200))
            node.set_position(x_pos, y_pos)

            # they start counting their ASes at 0. we start at 1
            node.set_asn(src_node.get_asn())

            #print('[DEBUG] adding node: %s' % str(node))
            self.__topology__.add_node(node.name, node)

            if ptp:
                # link between router and node
                link = PtpLink(src_node, None, node, None, {
                    # TODO: how to allocate bandwidth
                    # CORE: microsec
                    'delay': 125,
                    # TODO: how to allocate delay
                    # CORE: bps
                    'bw': 10000000,
                    })
            else:
                # link between switch and node
                link = PtpLink(switch, None, node, None, {
                    # TODO: how to allocate bandwidth
                    # CORE: microsec
                    'delay': 125,
                    # TODO: how to allocate delay
                    # CORE: bps
                    'bw': 10000000,
                    })

            self.__topology__.add_link(link)

