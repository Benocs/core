# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

class NetIDNodeMap():
    # key: netid (as int) - value: current node count of that netid.
    # first node is assigned id 1
    mapping = {}

    @staticmethod
    def register_node(nodeid, netid):
        if not netid in NetIDNodeMap.mapping:
            NetIDNodeMap.mapping[netid] = {}
        if not nodeid in NetIDNodeMap.mapping[netid]:
            if len(list(NetIDNodeMap.mapping[netid].values())) == 0:
                NetIDNodeMap.mapping[netid][nodeid] = 1
            else:
                NetIDNodeMap.mapping[netid][nodeid] = max(NetIDNodeMap.mapping[netid].values()) + 1

        return NetIDNodeMap.mapping[netid][nodeid]

