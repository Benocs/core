# various stub CORE services that exist solely to indicate different service
# classes a node implements
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import os

from core.service import CoreService, addservice
from core.misc.utils import *

class ServiceFlag(CoreService):
    _name = "serviceFlag"
    _group = "Service Flags"
    _depends = ()

class IGP(ServiceFlag):
    _name = "IGP"

addservice(IGP)

class EGP(ServiceFlag):
    _name = "EGP"

addservice(EGP)

class BGPRouteReflector(ServiceFlag):
    _name = "BGPRouteReflector"

addservice(BGPRouteReflector)

class Router(ServiceFlag):
    _name = "Router"

addservice(Router)

class DNSResolver(ServiceFlag):
    _name = "DNSResolver"

addservice(DNSResolver)

class DNSASRootServer(ServiceFlag):
    _name = "DNSASRootServer"

addservice(DNSASRootServer)

class DNSRootServer(ServiceFlag):
    _name = "DNSRootServer"

addservice(DNSRootServer)

class HTTPClient(ServiceFlag):
    _name = "HTTPClient"

addservice(HTTPClient)
