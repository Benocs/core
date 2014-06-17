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

class NetIDSubnetMap():
    """
        This class manages a mapping between known netids and their associated
        IP subnets. It takes a NetID as input and outputs the corresponding
        subnet-id. This id is then used by the ipaddr module to calculate
        subnet-prefixes from it.
    """

    __max_subnets_ipv4__ = 0x100
    __max_subnets_ipv6__ = 0x10000

    __mapping__ = {4:{}, 6:{}}

    @staticmethod
    def register_netid(netid, ipfam=4):
        if not ipfam == 4 and not ipfam == 6:
            raise ValueError("Invalid IP version: '%s'" % ipfam)

        if ipfam == 4:
            max_subnets = NetIDSubnetMap.__max_subnets_ipv4__
        elif ipfam == 6:
            max_subnets = NetIDSubnetMap.__max_subnets_ipv6__

        net_candidate = netid % max_subnets


        cnt = 0
        while net_candidate in NetIDSubnetMap.__mapping__[ipfam] and \
                not NetIDSubnetMap.__mapping__[ipfam][net_candidate] == netid:
            net_candidate = ((net_candidate + 1) % max_subnets)

            # failsafe switch in case no more subnets can be assigned
            cnt += 1
            if cnt > max_subnets:
                raise ValueError('There are no more free subnets available')

        # if we reach this, then no errors were encountered
        NetIDSubnetMap.__mapping__[ipfam][net_candidate] = netid

        return net_candidate

    @staticmethod
    def __repr__():
        outlist = []
        for ipfam in 4, 6:
            outlist.append('netid_subnet_map %d {\n' % ipfam)
            for subnet, netid in  NetIDSubnetMap.__mapping__[ipfam].items():
                outlist.append('    %d %d\n' % (netid, subnet))
            outlist.append('}\n\n')

        return ''.join(outlist)
