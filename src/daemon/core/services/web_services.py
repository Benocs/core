# various CORE services that implement functions for web-servers
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

class BaseWebService(CoreService):
    _name = "WebService"
    _group = "Utility"
    _depends = ()

class Lighttpd(BaseWebService):
    _name = "Lighttpd"
    _configs = ("/etc/lighttpd/lighttpd.conf",)
    _dirs = (("/etc/lighttpd", "union"), ("/var/www", "bind"),
            ("/var/cache/lighttpd", "bind"),
            ("/var/log/lighttpd", "bind"), ("/var/run", "bind"))
    _startup = ("service lighttpd start",)
    _shutdown = ("service lighttpd stop",)
    _verify = ("service lighttpd status",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        if filename == cls._configs[0]:
            return cls.generateLighttpdConf(node, filename)
        else:
            return ""

    @classmethod
    def generateLighttpdConf(cls, node, filename):
        # TODO: for now, only return default config
        return cls.generateDefaultLighttpdConf()

    @staticmethod
    def generateDefaultLighttpdConf():
        return """server.modules = (
    "mod_access",
    "mod_alias",
    "mod_compress",
    "mod_redirect",
    "mod_accesslog",
    "mod_status",
#   "mod_rewrite",
)

server.document-root        = "/var/www"
server.upload-dirs          = ("/var/cache/lighttpd/uploads")
server.errorlog             = "/var/log/lighttpd/error.log"
server.pid-file             = "/var/run/lighttpd.pid"
server.username             = "www-data"
server.groupname            = "www-data"
server.port                 = 80

accesslog.filename = "/var/log/lighttpd/access.log"

index-file.names            = ( "index.php", "index.html", "index.lighttpd.html" )
url.access-deny             = ( "~", ".inc" )
static-file.exclude-extensions = ( ".php", ".pl", ".fcgi" )

compress.cache-dir          = "/var/cache/lighttpd/compress/"
compress.filetype           = ( "application/javascript", "text/css", "text/html", "text/plain" )

status.status-url = "/server-status"

# default listening port for IPv6 falls back to the IPv4 port
include_shell "/usr/share/lighttpd/use-ipv6.pl " + server.port
include_shell "/usr/share/lighttpd/create-mime.assign.pl"
include_shell "/usr/share/lighttpd/include-conf-enabled.pl"
"""

addservice(Lighttpd)

