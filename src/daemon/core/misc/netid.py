# Copyright (c) 2014 Benocs GmbH
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
    def register_node(sessionid, nodeid, netid):
        if not sessionid in NetIDNodeMap.mapping:
            NetIDNodeMap.mapping[sessionid] = {}
        if not netid in NetIDNodeMap.mapping[sessionid]:
            NetIDNodeMap.mapping[sessionid][netid] = {}
        if not nodeid in NetIDNodeMap.mapping[sessionid][netid]:
            if len(list(NetIDNodeMap.mapping[sessionid][netid].values())) == 0:
                NetIDNodeMap.mapping[sessionid][netid][nodeid] = 1
            else:
                NetIDNodeMap.mapping[sessionid][netid][nodeid] = \
                        max(NetIDNodeMap.mapping[sessionid][netid].values()) + 1

        return NetIDNodeMap.mapping[sessionid][netid][nodeid]

class NetIDSubnetMap():
    """
        This class manages a mapping between known netids and their associated
        IP subnets. It takes a NetID as input and outputs the corresponding
        subnet-id. This id is then used by the ipaddr module to calculate
        subnet-prefixes from it.
    """

    __max_subnets_ipv4__ = 0x100
    __max_subnets_ipv6__ = 0x10000

    __mapping__ = {}

    @staticmethod
    def register_netid(sessionid, netid, ipfam=4):
        if not ipfam == 4 and not ipfam == 6:
            raise ValueError("Invalid IP version: '%s'" % ipfam)

        if not sessionid in NetIDSubnetMap.__mapping__:
            NetIDSubnetMap.__mapping__[sessionid] = {4:{}, 6:{}}

        if ipfam == 4:
            max_subnets = NetIDSubnetMap.__max_subnets_ipv4__
        elif ipfam == 6:
            max_subnets = NetIDSubnetMap.__max_subnets_ipv6__

        net_candidate = netid % max_subnets

        cnt = 0
        while net_candidate in NetIDSubnetMap.__mapping__[sessionid][ipfam] and \
                not NetIDSubnetMap.__mapping__[sessionid][ipfam][net_candidate] == netid:
            net_candidate = ((net_candidate + 1) % max_subnets)

            # failsafe switch in case no more subnets can be assigned
            cnt += 1
            if cnt > max_subnets:
                raise ValueError('There are no more free subnets available')

        # if we reach this, then no errors were encountered
        NetIDSubnetMap.__mapping__[sessionid][ipfam][net_candidate] = netid

        return net_candidate

    @staticmethod
    def clear_map(sessionid):
        if not sessionid in NetIDSubnetMap.__mapping__:
            return
        item = NetIDSubnetMap.__mapping__.pop(sessionid)
        del(item)

    @staticmethod
    def get_map_string(sessionid):
        if not sessionid in NetIDSubnetMap.__mapping__:
            raise ValueError(('sessionid: "%s" not found in NetIDSubnetMap' %
                    str(sessionid)))
        outlist = []

        for ipfam in 4, 6:
            outlist.append(('netid_subnet_map %d {\n' % (ipfam)))
            for subnet, netid in NetIDSubnetMap.__mapping__[sessionid][ipfam].items():
                outlist.append('    %d %d\n' % (netid, subnet))
            outlist.append('}\n\n')

        return ''.join(outlist)

    @staticmethod
    def __repr__():
        outlist = []
        for sessionid, sessionmap in NetIDSubnetMap.__mapping__.items():
            for ipfam in 4, 6:
                outlist.append(('netid_subnet_map sessionid: %d %d {\n' %
                    (ipfam, sessionid)))
                for subnet, netid in sessionmap[ipfam].items():
                    outlist.append('    %d %d\n' % (netid, subnet))
                outlist.append('}\n\n')

        return ''.join(outlist)
