#
# nodes - classes for managing network nodes
#         without needing to have a connection to a core-session
#
# Copyright (C) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

from core import pycore

from core.misc.ipaddr import isIPAddress, isIPv4Address, isIPv6Address


class CoreObj():
    corecls = None
    coreobj = None
    # state == True: node is up and running
    # state == False: node is down
    state = None

    def __init__(self):
        self.corecls = None
        self.coreobj = None
        self.state = False

    def set_corecls(self, cls):
        self.corecls = cls

    def get_corecls(self):
        return self.corecls

    def set_coreobj(self, obj):
        self.coreobj = obj

    def get_coreobj(self):
        return self.coreobj

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def register_with_core(self, session, server):
        raise NotImplementedError('Implement directly registering with core-daemon... later')
        """
        CoreNode:

        if session is None or server is None:
            return False

        if self.coreobj is None:
            self.coreobj = pycore.nodes.CoreNode(session=session, name=self.name, start=False)
        self.coreobj.setposition(x=self.x_pos, y=self.y_pos)

        services = []
        for service in services:
            self.coreobj.addservice(service)

        self.coreobj.type = self.nodetype

        flags = coreapi.CORE_API_ADD_FLAG
        self.coreobj.server = server
        session.broker.handlerawmsg(self.coreobj.tonodemsg(flags=flags))

        return True

        Interface:

        localname = 'n%s.%s.%s' % (self.coreobj.objid, key, session.sessionid)

        self.interfaces[key] = {
                'address': address,
                'core_obj': core_if_class(self.coreobj, name, localname, start=False)
                }
        self.interfaces[key]['core_obj'].addaddr(address)
        self.coreobj.addnetif(self.interfaces[key]['core_obj'], self.coreobj.newifindex())

        AS_Node:

        if session is None or server is None:
            return False

        if self.coreobj is None:
            self.coreobj = pycore.nodes.CoreNode(session=session, name=self.name, start=False)
        self.coreobj.setposition(x=self.x_pos, y=self.y_pos)

        " ""
        ## FIXME: TODO: next line is TMP only. fix it. this info should come from parsing nodes.conf
        if self.nodetype == 'igp_node':
            #services = [quagga.Zebra, quagga.Ospfv2, quagga.Ospfv3, quagga.Vtysh, utility.IPForwardService]
            services = [quagga.Zebra, mbgp.MOspfv2, quagga.Ospfv3, quagga.Vtysh, utility.IPForwardService]
        elif self.nodetype == 'egp_node':
            #services = [quagga.Zebra, quagga.Ospfv2, quagga.Ospfv3, quagga.Bgp, quagga.Vtysh, utility.IPForwardService]
            services = [quagga.Zebra, mbgp.MBgp, mbgp.MOspfv2, quagga.Vtysh,
                    utility.IPForwardService, monitoring.NetFlow9ProbeService]
        elif self.nodetype == 'netflow9collector':
            services = [monitoring.NetFlow9SinkService]
        elif self.nodetype == 'CE':
            services = [monitoring.NetFlow9SinkService]
        elif self.nodetype == 'server':
            services = [utility.DefaultRouteService]
        elif self.nodetype == 'client':
            services = [utility.DefaultRouteService]
        else:
        " ""
        services = []
        for service in services:
            self.coreobj.addservice(service)

        self.coreobj.type = self.nodetype

        if self.as_number > 0:
            self.coreobj.setnetid(self.as_number)


        flags = coreapi.CORE_API_ADD_FLAG
        self.coreobj.server = server
        session.broker.handlerawmsg(self.coreobj.tonodemsg(flags=flags))

        return True

        (PtP)Link:

        if session is None or server is None:
            return False

        #if self.src_interface is None or self.dst_interface is None:
        #    return False

        if self.coreobj is None:
            self.coreobj = self.corecls(session=session, name=None, start=False)

        " "" possible keys, values are:
                delay: int64 microseconds
                bw: int64 bps (bits per second)
                loss: string percent
                duplicate: string percent (max. 50)
                jitter: int32 random delay microseconds
        " ""
        for key, value in self.properties.items():
            self.src_interface['core_obj'].setparam(key, value)
            self.dst_interface['core_obj'].setparam(key, value)

        self.coreobj.attach(self.src_interface['core_obj'])
        self.coreobj.attach(self.dst_interface['core_obj'])

        flags = coreapi.CORE_API_ADD_FLAG
        self.coreobj.server = server
        for msg in self.coreobj.tolinkmsgs(flags=flags):
            session.broker.handlerawmsg(msg)

        return True

        """

class Interface(CoreObj):

    __name__ = None
    __key__ = None
    __addresses__ = None

    def __init__(self, name, addresses, key=None):
        super().__init__()

        if not addresses is None and not isinstance(addresses, list):
            raise ValueError('Interface addresses is not a list')

        self.__name__ = name

        if addresses is None:
            self.__addresses__ = []
        else:
            self.__addresses__ = addresses

        if not key is None:
            self.__key__ = key

        #print('[DEBUG] created %s' % str(self))

    def __repr__(self):
        return '<Interface: addresses: %s>' % (', '.join(['%s' % addr.__repr__() \
                for addr in self.__addresses__]))

    def add_addr(self, address):
        if not isinstance(address, list):
            address = [address]
        for addr in address:
            if isIPAddress(addr):
                if not address in self.__addresses__:
                    self.__addresses__.append(address)
            else:
                raise ValueError('Not an IP address: %s' % str(addr))

    def remove_addr(self, address):
        if address in self.__addresses__:
            self.__addresses__.pop(self.__addresses__.index(address))

    def get_addresses(self):
        return self.__addresses__

    def get_ipv4_addresses(self):
        return [addr for addr in self.__addresses__ if isIPv4Address(addr)]

    def get_ipv6_addresses(self):
        #print('[DEBUG] all  addresses: %s' % str(self.__addresses__))
        #print('[DEBUG] IPv6 addresses: %s' % str([addr for addr in self.__addresses__ if
        #    isIPv6Address(addr)]))
        return [addr for addr in self.__addresses__ if isIPv6Address(addr)]

    def set_key(self, key):
        self.__key__ = key

    def get_key(self):
        return self.__key__

    def set_name(self, name):
        self.__name__ = name

    def get_name(self):
        return self.__name__

class CoreNode(CoreObj):

    __next_node_id__ = 1

    name = None
    interfaces = None
    # CORE node model as defined in nodes.conf
    nodemodel = None
    # CORE node type as defined in nodes.conf
    nodetype = None
    # internal tag that describes the purpose of a node
    # valid values: igp, egp, server, client, dns
    nodetag = None
    nodeid = None

    x_pos = None
    y_pos = None

    def __init__(self, name):
        super().__init__()

        self.name = name
        self.interfaces = {}
        self.nodemodel = 'router'
        self.nodetype = 'router'
        self.nodetag = ''
        self.nodeid = 'n%d' % CoreNode.__next_node_id__
        CoreNode.__next_node_id__ += 1

        self.x_pos = None
        self.y_pos = None

    def __repr__(self):
        return ('Node: id: %s, name: %s, type: %s, model: %s, interfaces: %s' %
                (str(self.nodeid), str(self.name), str(self.nodetype),
                    str(self.nodemodel), str(self.interfaces)))

    def create_interface(self, addresses, idx=-1, name=None):
        if not name is None:
            key = name
        elif not idx == -1:
            key = str(idx)
        else:
            key = str(len(self.interfaces))

        if name is None:
            name = 'eth%s' % str(key)

        ifc = Interface(name, addresses, key)

        if not key in self.interfaces:
            self.interfaces[key] = ifc
        else:
            self.interfaces[key].add_addr(addresses)

        return self.interfaces[key]

    def remove_interface(self, interface):
        if interface is None:
            raise ValueError('interface cannot be None')

        found = False
        key, value = None, None
        for k, v in self.interfaces.items():
            if interface == v:
                found = True
                key, value = k, v
                break
        if found:
            self.interfaces.pop(key)

    def get_interfaces(self):
        return self.interfaces.values()

    def get_interface_by_key(self, key):
        if key is None:
            raise ValueError('key cannot be None')

        if not key in self.interfaces:
            raise ValueError('key not found')

        return self.interfaces[key]

    def get_interface_by_name(self, name):
        if name is None:
            raise ValueError('name cannot be None')

        for interface in self.interfaces.values():
            if interface.get_name() == name:
                return interface

        raise ValueError('no interface found with name: %s' % name)

    def get_interface_key(self, interface):
        if interface is None:
            raise ValueError('interface cannot be None')

        found = False
        key, value = None, None
        for k, v in self.interfaces.items():
            if interface == v:
                found = True
                key, value = k, v
                break
        if found:
            return key
        else:
            return None

    def set_name(self, name):
        self.name = name

    def get_name(self):
        return self.name

    def set_model(self, nodemodel):
        self.nodemodel = nodemodel

    def get_model(self):
        return self.nodemodel

    def set_type(self, nodetype):
        self.nodetype = nodetype

    def get_type(self):
        return self.nodetype

    def set_tag(self, nodetag):
        self.nodetag = nodetag

    def get_tag(self):
        return self.nodetag

    def set_position(self, x_pos, y_pos):
        self.x_pos = x_pos
        self.y_pos = y_pos

    def get_position(self):
        return (self.x_pos, self.y_pos)

class ASNode(CoreNode):

    as_number = None

    def __init__(self, name):
        super().__init__(name)
        self.nodemodel = 'as_node'
        self.as_number = 1

    def __repr__(self):
        return '%s, ASN: %s' % (super().__repr__(), str(self.as_number))

    def set_asn(self, as_number):
        self.as_number = as_number

    def get_asn(self):
        return self.as_number

class ServerNode(ASNode):

    def __init__(self, name):
        super().__init__(name)
        self.nodemodel = 'server'

class AccessNode(ASNode):

    def __init__(self, name):
        super().__init__(name)
        self.nodemodel = 'client'

class SwitchNode(ASNode):

    def __init__(self, name):
        super().__init__(name)
        self.nodetype = 'lanswitch'
        self.nodemodel = 'switch_node'

class DNSServer(ASNode):

    def __init__(self, name):
        super().__init__(name)
        self.nodemodel = 'dnsserver'

class DNSASServer(ASNode):

    def __init__(self, name):
        super().__init__(name)
        self.nodemodel = 'as_auth_dnsserver'

class DNSRootServer(ASNode):

    def __init__(self, name):
        super().__init__(name)
        self.nodemodel = 'dnsrootserver'

class Link(CoreObj):

    # nodes is a list of tuples(node, interface)
    nodes = None
    properties = None

    def __init__(self, nodes, properties=None, corecls=None):
        super().__init__()

        if not isinstance(nodes, list):
            raise ValueError('nodes needs to be a list')

        if not len(nodes) >= 2:
            raise ValueError('a link needs to have at least two nodes attached to it')

        if not isinstance(nodes[0], tuple):
            raise ValueError('nodes need to be a tuple of (node, interface)')

        self.nodes = nodes

        if properties is None:
            self.properties = {}
        else:
            self.properties = properties

    def __repr__(self):
        nodesstr = ', '.join(['(%s, %s)' % (node[0].get_name(), node[1]) for node in self.nodes\
                if not node[0] is None])
        return '<Link: nodes: %s, properties: %s>' % (nodesstr, str(self.properties))

    def add_interface(self, node, interface):
        """ adds an interface of a node to the link """

        if not (node, interface) in self.nodes:
            self.nodes.append((node, interface))
            # if a 'placeholder' (this node without an interface for this link) is
            # encountered, delete it
            if interface is not None and (node, None) in self.nodes:
                self.remove_interface(node, None)

    def remove_interface(self, node, interface):
        """ removes an interface of a node from the link """
        if (node, interface) in self.nodes:
            self.nodes.pop(self.nodes.index((node, interface)))

    def get_interfaces(self):
        return [intf for node, intf in self.nodes]

    def get_nodes(self):
        return [node for node, intf in self.nodes]

class PtpLink(Link):

    def __init__(self, src_node=None, src_interface=None,
            dst_node=None, dst_interface=None,
            properties=None):

        if src_node is None or dst_node is None:
            raise ValueError('a point-to-point link needs two nodes')

        super().__init__([(src_node, src_interface),
            (dst_node, dst_interface)], properties)

        self.corecls = pycore.nodes.PtpNet

    def set_src(self, src_node, src_interface):
        if len(self.nodes) >= 2:
            self.nodes.pop(0)
        self.nodes.insert(0, (src_node, src_interface))

    def set_dst(self, dst_node, dst_interface):
        if len(self.nodes) >= 2:
            self.nodes.pop(1)
        self.nodes.append((dst_node, dst_interface))

    def get_src(self):
        if len(self.nodes) >= 2:
            return self.nodes[0]

    def get_dst(self):
        if len(self.nodes) >= 2:
            return self.nodes[1]

    def get_src_node(self):
        if len(self.nodes) >= 2:
            return self.nodes[0][0]

    def get_dst_node(self):
        if len(self.nodes) >= 2:
            return self.nodes[1][0]

    def get_src_interface(self):
        if len(self.nodes) >= 2:
            return self.nodes[0][1]

    def get_dst_interface(self):
        if len(self.nodes) >= 2:
            return self.nodes[1][1]
