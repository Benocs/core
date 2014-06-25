#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

from core.api import coreapi
from core.conf import ConfigurableManager, Configurable
from core.misc.netid import NetIDSubnetMap

class NetIDSubnetMapManager(ConfigurableManager):
    _name = "NetIDSubnetMapManager"
    _type = coreapi.CORE_TLV_REG_UTILITY

    def __init__(self, session):
        super().__init__(session)
        self.verbose = self.session.getcfgitembool('verbose', False)
        self.register()

    def register(self):
        """ Register models as configurable object(s) with the Session object.
        """
        models = [NetIDSubnetMapIPv4, NetIDSubnetMapIPv6]
        for m in models:
            self.session.addconfobj(m._name, m._type, m.cfg_callback)

    def clear(self):
        models = [NetIDSubnetMapIPv4, NetIDSubnetMapIPv6]
        for m in models:
            m.clear_session(self.session)

    @classmethod
    def toconfmsg(cls, flags, nodenum, typeflags, values):
        raise NotImplementedError("use toconfmsgs() instead")

    def toconfmsgs(self, flags=None, nodenum=None, typeflags=None, values=None):
        msgs = []

        if flags is None:
            flags = 0
        if typeflags is None:
            typeflags = coreapi.CONF_TYPE_FLAGS_UPDATE

        models = [NetIDSubnetMapIPv4, NetIDSubnetMapIPv6]
        for m in models:
            msgs.append(m.toconfmsg(flags, nodenum, typeflags, values,
                    self.session))
        return msgs

class BaseNetIDSubnetMap(Configurable):

    _type = coreapi.CORE_TLV_REG_UTILITY
    _bitmap = None
    _name = None
    __ipversion__ = None
    __data_type__ = coreapi.CONF_DATA_TYPE_UINT32

    def __init__(self, session, objid, verbose=False, values=None):
        super().__init__(self, session, objid)
        self.verbose = verbose

    @classmethod
    def cfg_callback(cls, session, msg):
        values_str = msg.gettlv(coreapi.CORE_TLV_CONF_VALUES)
        if not values_str is None:
            if not session.sessionid in NetIDSubnetMap.__mapping__:
                NetIDSubnetMap.__mapping__[session.sessionid] = {}
                NetIDSubnetMap.__mapping__[session.sessionid][4] = {}
                NetIDSubnetMap.__mapping__[session.sessionid][6] = {}
            # clear old map
            else:
                NetIDSubnetMap.__mapping__[session.sessionid][cls.__ipversion__] = {}

            values = values_str.split('|')
            idx = 0
            while (idx+1) < len(values):
                subnet = int(values[idx])
                netid = int(values[idx+1])
                NetIDSubnetMap.__mapping__[session.sessionid][cls.__ipversion__][subnet] = netid
                idx += 2

    @classmethod
    def clear_session(cls, session):
        NetIDSubnetMap.clear_map(session.sessionid)

    @classmethod
    def toconfmsg(cls, flags, nodenum, typeflags, values, session):
        tlvdata = b''
        tlvdata += coreapi.CoreConfTlv.pack(coreapi.CORE_TLV_CONF_OBJ,
                cls._name)
        tlvdata += coreapi.CoreConfTlv.pack(coreapi.CORE_TLV_CONF_TYPE,
                typeflags)
        datatypes = tuple(cls.__data_type__
                for x in NetIDSubnetMap.__mapping__[session.sessionid][cls.__ipversion__])
        tlvdata += coreapi.CoreConfTlv.pack(coreapi.CORE_TLV_CONF_DATA_TYPES,
                datatypes)
        values_str = '|'.join(str(x) for x in d.values())
        tlvdata += coreapi.CoreConfTlv.pack(coreapi.CORE_TLV_CONF_VALUES,
                values_str)

        msg = coreapi.CoreConfMessage.pack(flags, tlvdata)
        return msg


class NetIDSubnetMapIPv4(BaseNetIDSubnetMap):

    _name = 'netid_subnet_map_ipv4'
    __ipversion__ = 4

class NetIDSubnetMapIPv6(BaseNetIDSubnetMap):

    _name = 'netid_subnet_map_ipv6'
    __ipversion__ = 6

