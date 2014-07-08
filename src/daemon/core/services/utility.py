#
# CORE
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# author: Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

'''
utility.py: defines miscellaneous utility services.
'''

import os

from core.service import CoreService, addservice
from core.misc.ipaddr import IPv4Prefix, IPv6Prefix, IPv4Addr
from core.misc.ipaddr import isIPAddress, isIPv4Address, isIPv6Address
from core.misc.utils import *
from core.constants import *

from core.services import service_flags

class UtilService(CoreService):
    ''' Parent class for utility services.
    '''
    _name = "UtilityProcess"
    _group = "Utility"
    _depends = ()
    _dirs = ()
    _configs = ()
    _startindex = 80
    _startup = ()
    _shutdown = ()

    @classmethod
    def generateconfig(cls,  node, filename, services):
        return ""

class IPForwardService(UtilService):
    _name = "IPForward"
    _configs = ("ipforward.sh", )
    _startindex = 5
    _startup = ("sh ipforward.sh", )

    @classmethod
    def generateconfig(cls, node, filename, services):
        if os.uname()[0] == "Linux":
            return cls.generateconfiglinux(node, filename, services)
        elif os.uname()[0] == "FreeBSD":
            return cls.generateconfigbsd(node, filename, services)
        else:
            raise Exception("unknown platform")

    @classmethod
    def generateconfiglinux(cls, node, filename, services):
        cfg = ['#!/bin/sh\n',
                '# auto-generated by IPForward service (utility.py)\n']

        if node.enable_ipv4:
            cfg.extend([
                    '%s -w net.ipv4.conf.all.forwarding=1\n' % SYSCTL_BIN,
                    '%s -w net.ipv4.conf.all.send_redirects=0\n' % SYSCTL_BIN,
                    '%s -w net.ipv4.conf.all.rp_filter=0\n' % SYSCTL_BIN,
                    '%s -w net.ipv4.conf.default.rp_filter=0\n' % SYSCTL_BIN,
                    ])
        else:
            cfg.extend([
                    '%s -w net.ipv4.conf.all.forwarding=0\n' % SYSCTL_BIN,
                    '%s -w net.ipv4.conf.all.send_redirects=0\n' % SYSCTL_BIN,
                    '%s -w net.ipv4.conf.all.rp_filter=1\n' % SYSCTL_BIN,
                    '%s -w net.ipv4.conf.default.rp_filter=1\n' % SYSCTL_BIN,
                    ])

        if node.enable_ipv6:
            cfg.extend([
                    '%s -w net.ipv6.conf.all.forwarding=1\n' % SYSCTL_BIN,
                    ])
        else:
            cfg.extend([
                    '%s -w net.ipv6.conf.all.forwarding=0\n' % SYSCTL_BIN,
                    ])

        for ifc in node.netifs():
            name = sysctldevname(ifc.name)
            cfg += "%s -w net.ipv4.conf.%s.send_redirects=0\n" % \
                    (SYSCTL_BIN, name)
            if node.enable_ipv4:
                cfg += "%s -w net.ipv4.conf.%s.forwarding=1\n" % (SYSCTL_BIN, name)
                cfg += "%s -w net.ipv4.conf.%s.rp_filter=0\n" % (SYSCTL_BIN, name)
            else:
                cfg += "%s -w net.ipv4.conf.%s.forwarding=0\n" % (SYSCTL_BIN, name)
                cfg += "%s -w net.ipv4.conf.%s.rp_filter=1\n" % (SYSCTL_BIN, name)
        return ''.join(cfg)

    @classmethod
    def generateconfigbsd(cls, node, filename, services):
        cfg = ['#!/bin/sh\n',
                '# auto-generated by IPForward service (utility.py)\n']

        if node.enable_ipv4:
            cfg.extend([
                    '%s -w net.inet.ip.forwarding=1\n' % SYSCTL_BIN,
                    '%s -w net.inet.icmp.bmcastecho=1\n' % SYSCTL_BIN,
                    '%s -w net.inet.icmp.icmplim=0\n' % SYSCTL_BIN,
                    ])
        else:
            cfg.extend([
                    '%s -w net.inet.ip.forwarding=0\n' % SYSCTL_BIN,
                    '%s -w net.inet.icmp.bmcastecho=0\n' % SYSCTL_BIN,
                    '%s -w net.inet.icmp.icmplim=0\n' % SYSCTL_BIN,
                    ])

        if node.enable_ipv6:
            cfg.append('%s -w net.inet6.ip6.forwarding=1\n'  % SYSCTL_BIN)
        else:
            cfg.append('%s -w net.inet6.ip6.forwarding=0\n'  % SYSCTL_BIN)

        return ''.join(cfg)

addservice(IPForwardService)

class DefaultRouteService(UtilService):
    _name = "DefaultRoute"
    _configs = ("defaultroute.sh",)
    _startup = ("sh defaultroute.sh",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        cfg = "#!/bin/sh\n"
        cfg += "# auto-generated by DefaultRoute service (utility.py)\n"
        for ifc in node.netifs():
            for idx, net_netif in list(ifc.net._netif.items()):
                # do not include control interfaces
                if hasattr(ifc, 'control') and ifc.control == True:
                    continue

                # skip our own interface
                if ifc == net_netif:
                    continue

                for addr in net_netif.addrlist:
                    # only core routers are candidate gateways
                    if not service_flags.Router in net_netif.node.services:
                        continue
                    if node.enable_ipv4 and isIPv4Address(addr):
                        cfg += cls.addrstr(addr)
                    if node.enable_ipv6 and isIPv6Address(addr):
                        cfg += cls.addrstr(addr)
        return cfg

    @staticmethod
    def addrstr(x):
        if x.find(":") >= 0:
            net = IPv6Prefix(x)
            fam = "inet6 ::"
        else:
            net = IPv4Prefix(x)
            fam = "inet 0.0.0.0"
        if os.uname()[0] == "Linux":
            rtcmd = "ip route add default via"
        elif os.uname()[0] == "FreeBSD":
            rtcmd = "route add -%s" % fam
        else:
            raise Exception("unknown platform")
        return "%s %s\n" % (rtcmd, x.split('/')[0])

addservice(DefaultRouteService)

class StaticRouteToLoopback(UtilService):
    _name = "StaticRouteToLoopback"
    _configs = ("staticroutetoloopbackdummy.sh",)
    _startup = ("sh staticroutetoloopbackdummy.sh",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        cfg = "# auto-generated by StaticRouteToLoopback dummy service (utility.py)\n"
        for ifc in node.netifs():
            for idx, net_netif in list(ifc.net._netif.items()):
                # do not include control interfaces
                if hasattr(ifc, 'control') and ifc.control == True:
                    continue

                # skip all own interface(s)
                if ifc == net_netif:
                    continue

                # only core routers are candidate gateways
                if not service_flags.Router in net_netif.node.services:
                    continue

                for addr in ifc.addrlist:
                    if node.enable_ipv4 and isIPv4Address(addr):
                        route_target = node.getLoopbackIPv4()
                    elif node.enable_ipv6 and isIPv6Address(addr):
                        route_target = node.getLoopbackIPv6()
                    else:
                        continue

                    print(('[%s] ip r a %s via %s' % (str(cls),
                            str(route_target), str(addr.split('/')[0]))))
                    net_netif.node.cmd(['ip', 'route', 'add', str(route_target),
                            'via', addr.split('/')[0]])
                    cfg += ' '.join(['#ip', 'route', 'add', str(route_target),
                            'via', addr.split('/')[0], '\n'])
        return cfg

addservice(StaticRouteToLoopback)

class DefaultMulticastRouteService(UtilService):
    _name = "DefaultMulticastRoute"
    _configs = ("defaultmroute.sh",)
    _startup = ("sh defaultmroute.sh",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        cfg = "#!/bin/sh\n"
        cfg += "# auto-generated by DefaultMulticastRoute service (utility.py)\n"
        cfg += "# the first interface is chosen below; please change it "
        cfg += "as needed\n"

        if not node.enable_ipv4:
            return cfg

        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            if os.uname()[0] == "Linux":
                rtcmd = "ip route add 224.0.0.0/4 dev"
            elif os.uname()[0] == "FreeBSD":
                rtcmd = "route add 224.0.0.0/4 -iface"
            else:
                raise Exception("unknown platform")
            cfg += "%s %s\n" % (rtcmd, ifc.name)
            cfg += "\n"
            break
        return cfg

addservice(DefaultMulticastRouteService)

class StaticRouteService(UtilService):
    _name = "StaticRoute"
    _configs = ("staticroute.sh",)
    _startup = ("sh staticroute.sh",)
    _custom_needed = True

    @classmethod
    def generateconfig(cls, node, filename, services):
        cfg = "#!/bin/sh\n"
        cfg += "# auto-generated by StaticRoute service (utility.py)\n#\n"
        cfg += "# NOTE: this service must be customized to be of any use\n"
        cfg += "#       Below are samples that you can uncomment and edit.\n#\n"
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            cfg += "\n".join(map(cls.routestr, ifc.addrlist))
            cfg += "\n"
        return cfg

    @staticmethod
    def routestr(x):
        if x.find(":") >= 0:
            net = IPv6Prefix(x)
            fam = "inet6"
            dst = "3ffe:4::/64"
        else:
            net = IPv4Prefix(x)
            fam = "inet"
            dst = "10.9.8.0/24"
        if net.maxaddr() == net.minaddr():
            return ""
        else:
            if os.uname()[0] == "Linux":
                rtcmd = "#/sbin/ip route add %s via" % dst
            elif os.uname()[0] == "FreeBSD":
                rtcmd = "#/sbin/route add -%s %s" % (fam, dst)
            else:
                raise Exception("unknown platform")
            return "%s %s" % (rtcmd, net.minaddr())

addservice(StaticRouteService)

class SshService(UtilService):
    _name = "SSH"
    if os.uname()[0] == "FreeBSD":
        _configs = ("startsshd.sh", "sshd_config",)
        _dirs = ()
    else:
        _configs = ("startsshd.sh", "/etc/ssh/sshd_config",)
        _dirs = ("/etc/ssh", "/var/run/sshd",)
    _startup = ("sh startsshd.sh",)
    _shutdown = ("killall sshd",)
    _validate = ()

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Use a startup script for launching sshd in order to wait for host
            key generation.
        '''
        if os.uname()[0] == "FreeBSD":
            sshcfgdir = node.nodedir
            sshstatedir = node.nodedir
            sshlibdir = "/usr/libexec"
        else:
            sshcfgdir = cls._dirs[0]
            sshstatedir = cls._dirs[1]
            sshlibdir = "/usr/lib/openssh"
        if filename == "startsshd.sh":
            return """\
#!/bin/sh
# auto-generated by SSH service (utility.py)
ssh-keygen -q -t rsa -N "" -f %s/ssh_host_rsa_key
chmod 655 %s
# wait until RSA host key has been generated to launch sshd
/usr/sbin/sshd -f %s/sshd_config
""" % (sshcfgdir, sshstatedir, sshcfgdir)
        else:
            return """\
# auto-generated by SSH service (utility.py)
Port 22
Protocol 2
HostKey %s/ssh_host_rsa_key
UsePrivilegeSeparation yes
PidFile %s/sshd.pid

KeyRegenerationInterval 3600
ServerKeyBits 768

SyslogFacility AUTH
LogLevel INFO

LoginGraceTime 120
PermitRootLogin yes
StrictModes yes

RSAAuthentication yes
PubkeyAuthentication yes

IgnoreRhosts yes
RhostsRSAAuthentication no
HostbasedAuthentication no

PermitEmptyPasswords no
ChallengeResponseAuthentication no

X11Forwarding yes
X11DisplayOffset 10
PrintMotd no
PrintLastLog yes
TCPKeepAlive yes

AcceptEnv LANG LC_*
Subsystem sftp %s/sftp-server
UsePAM yes
UseDNS no
""" % (sshcfgdir, sshstatedir, sshlibdir)

addservice(SshService)

class DhcpService(UtilService):
    _name = "DHCP"
    _configs = ("/etc/dhcp/dhcpd.conf",)
    _dirs = ("/etc/dhcp",)
    _startup = ("dhcpd",)
    _shutdown = ("killall dhcpd",)
    _validate = ("pidof dhcpd",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Generate a dhcpd config file using the network address of
            each interface.
        '''
        cfg = """\
# auto-generated by DHCP service (utility.py)
# NOTE: move these option lines into the desired pool { } block(s) below
#option domain-name "test.com";
#option domain-name-servers 10.0.0.1;
#option routers 10.0.0.1;

log-facility local6;

default-lease-time 600;
max-lease-time 7200;

ddns-update-style none;
"""
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            cfg += "\n".join(map(cls.subnetentry, ifc.addrlist))
            cfg += "\n"
        return cfg

    @staticmethod
    def subnetentry(x):
        ''' Generate a subnet declaration block given an IPv4 prefix string
            for inclusion in the dhcpd3 config file.
        '''
        # IPv6 not supported in v4 dhcpd
        if x.find(":") >= 0:
            return ""
        else:
            addr = x.split("/")[0]
            net = IPv4Prefix(x)
            # divide the address space in half TODO: why divide in half? addr+1 sounds so much better
            #rangelow = net.addr(net.numaddr() / 2)
            rangelow = net.addr(IPv4Addr(addr) + 1)
            rangehigh = net.maxaddr()
            return """
subnet %s netmask %s {
  pool {
    range %s %s;
    default-lease-time 600;
    option routers %s;
  }
}
""" % (net.prefixstr(), net.netmaskstr(), rangelow, rangehigh, addr)

addservice(DhcpService)

class DhcpClientService(UtilService):
    ''' Use a DHCP client for all interfaces for addressing.
    '''
    _name = "DHCPClient"
    _configs = ("startdhcpclient.sh",)
    _startup = ("sh startdhcpclient.sh",)
    _shutdown = ("killall dhclient",)
    _validate = ("pidof dhclient",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Generate a script to invoke dhclient on all interfaces.
        '''
        cfg = "#!/bin/sh\n"
        cfg += "# auto-generated by DHCPClient service (utility.py)\n"
        cfg += "# uncomment this mkdir line and symlink line to enable client-"
        cfg += "side DNS\n# resolution based on the DHCP server response.\n"
        cfg += "#mkdir -p /var/run/resolvconf/interface\n"

        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            cfg += "#ln -s /var/run/resolvconf/interface/%s.dhclient" % ifc.name
            cfg += " /var/run/resolvconf/resolv.conf\n"
            cfg += "/sbin/dhclient -nw -pf /var/run/dhclient-%s.pid" % ifc.name
            cfg += " -lf /var/run/dhclient-%s.lease %s\n" % (ifc.name,  ifc.name)
        return cfg

addservice(DhcpClientService)

class FtpService(UtilService):
    ''' Start a vsftpd server.
    '''
    _name = "FTP"
    _configs = ("vsftpd.conf",)
    _dirs = ("/var/run/vsftpd/empty", "/var/ftp",)
    _startup = ("vsftpd ./vsftpd.conf",)
    _shutdown = ("killall vsftpd",)
    _validate = ("pidof vsftpd",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Generate a vsftpd.conf configuration file.
        '''
        return """\
# vsftpd.conf auto-generated by FTP service (utility.py)
listen=YES
anonymous_enable=YES
local_enable=YES
dirmessage_enable=YES
use_localtime=YES
xferlog_enable=YES
connect_from_port_20=YES
xferlog_file=/var/log/vsftpd.log
ftpd_banner=Welcome to the CORE FTP service
secure_chroot_dir=/var/run/vsftpd/empty
anon_root=/var/ftp
"""

addservice(FtpService)

class HttpService(UtilService):
    ''' Start an apache server.
    '''
    _name = "HTTP"
    _configs = ("/etc/apache2/apache2.conf", "/etc/apache2/envvars",
                "/var/www/index.html",)
    _dirs = ("/etc/apache2", "/var/run/apache2", "/var/log/apache2",
             "/run/lock", "/var/lock/apache2", "/var/www", )
    _startup = ("chown www-data /var/lock/apache2", "apache2ctl start",)
    _shutdown = ("apache2ctl stop",)
    _validate = ("pidof apache2",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Generate an apache2.conf configuration file.
        '''
        if filename == cls._configs[0]:
            return cls.generateapache2conf(node, filename, services)
        elif filename == cls._configs[1]:
            return cls.generateenvvars(node, filename, services)
        elif filename == cls._configs[2]:
            return cls.generatehtml(node, filename, services)
        else:
            return ""

    @classmethod
    def generateapache2conf(cls, node, filename, services):
        return """\
# apache2.conf generated by utility.py:HttpService
LockFile ${APACHE_LOCK_DIR}/accept.lock
PidFile ${APACHE_PID_FILE}
Timeout 300
KeepAlive On
MaxKeepAliveRequests 100
KeepAliveTimeout 5

<IfModule mpm_prefork_module>
    StartServers          5
    MinSpareServers       5
    MaxSpareServers      10
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>

<IfModule mpm_worker_module>
    StartServers          2
    MinSpareThreads      25
    MaxSpareThreads      75
    ThreadLimit          64
    ThreadsPerChild      25
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>

<IfModule mpm_event_module>
    StartServers          2
    MinSpareThreads      25
    MaxSpareThreads      75
    ThreadLimit          64
    ThreadsPerChild      25
    MaxClients          150
    MaxRequestsPerChild   0
</IfModule>

User ${APACHE_RUN_USER}
Group ${APACHE_RUN_GROUP}

AccessFileName .htaccess

<Files ~ "^\.ht">
    Order allow,deny
    Deny from all
    Satisfy all
</Files>

DefaultType None

HostnameLookups Off

ErrorLog ${APACHE_LOG_DIR}/error.log
LogLevel warn

#Include mods-enabled/*.load
#Include mods-enabled/*.conf
LoadModule alias_module /usr/lib/apache2/modules/mod_alias.so
LoadModule auth_basic_module /usr/lib/apache2/modules/mod_auth_basic.so
LoadModule authz_default_module /usr/lib/apache2/modules/mod_authz_default.so
LoadModule authz_host_module /usr/lib/apache2/modules/mod_authz_host.so
LoadModule authz_user_module /usr/lib/apache2/modules/mod_authz_user.so
LoadModule autoindex_module /usr/lib/apache2/modules/mod_autoindex.so
LoadModule dir_module /usr/lib/apache2/modules/mod_dir.so
LoadModule env_module /usr/lib/apache2/modules/mod_env.so

NameVirtualHost *:80
Listen 80

<IfModule mod_ssl.c>
    Listen 443
</IfModule>
<IfModule mod_gnutls.c>
    Listen 443
</IfModule>

LogFormat "%v:%p %h %l %u %t \\"%r\\" %>s %O \\"%{Referer}i\\" \\"%{User-Agent}i\\"" vhost_combined
LogFormat "%h %l %u %t \\"%r\\" %>s %O \\"%{Referer}i\\" \\"%{User-Agent}i\\"" combined
LogFormat "%h %l %u %t \\"%r\\" %>s %O" common
LogFormat "%{Referer}i -> %U" referer
LogFormat "%{User-agent}i" agent

ServerTokens OS
ServerSignature On
TraceEnable Off

<VirtualHost *:80>
	ServerAdmin webmaster@localhost
	DocumentRoot /var/www
	<Directory />
		Options FollowSymLinks
		AllowOverride None
	</Directory>
	<Directory /var/www/>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	</Directory>
	ErrorLog ${APACHE_LOG_DIR}/error.log
	LogLevel warn
	CustomLog ${APACHE_LOG_DIR}/access.log combined
</VirtualHost>

"""

    @classmethod
    def generateenvvars(cls, node, filename, services):
        return """\
# this file is used by apache2ctl - generated by utility.py:HttpService
# these settings come from a default Ubuntu apache2 installation
export APACHE_RUN_USER=www-data
export APACHE_RUN_GROUP=www-data
export APACHE_PID_FILE=/var/run/apache2.pid
export APACHE_RUN_DIR=/var/run/apache2
export APACHE_LOCK_DIR=/var/lock/apache2
export APACHE_LOG_DIR=/var/log/apache2
export LANG=C
export LANG
"""

    @classmethod
    def generatehtml(cls, node, filename, services):
        body = """\
<!-- generated by utility.py:HttpService -->
<h1>%s web server</h1>
<p>This is the default web page for this server.</p>
<p>The web server software is running but no content has been added, yet.</p>
""" % node.name
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            body += "<li>%s - %s</li>\n" % (ifc.name, ifc.addrlist)
        return "<html><body>%s</body></html>" % body

addservice(HttpService)

class PcapService(UtilService):
    ''' Pcap service for logging packets.
    '''
    _name = "pcap"
    _configs = ("pcap.sh", )
    _dirs = ()
    _startindex = 1
    _startup = ("sh pcap.sh start",)
    _shutdown = ("sh pcap.sh stop",)
    _validate = ("pidof tcpdump",)
    _meta = "logs network traffic to pcap packet capture files"

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Generate a startpcap.sh traffic logging script.
        '''
        cfg = """
#!/bin/sh
# set tcpdump options here (see 'man tcpdump' for help)
# (-s snap length, -C limit pcap file length, -n disable name resolution)
DUMPOPTS="-s 12288 -C 10 -n"

if [ "x$1" = "xstart" ]; then

"""
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                cfg += '# '
            redir = "< /dev/null"
            cfg += "tcpdump ${DUMPOPTS} -w %s.%s.pcap -i %s %s &\n" % \
                    (node.name, ifc.name, ifc.name, redir)
        cfg += """

elif [ "x$1" = "xstop" ]; then
    mkdir -p ${SESSION_DIR}/pcap
    mv *.pcap ${SESSION_DIR}/pcap
fi;
"""
        return cfg

addservice(PcapService)

class RadvdService(UtilService):
    _name = "radvd"
    _configs = ("/etc/radvd/radvd.conf",)
    _dirs = ("/etc/radvd",)
    _startup = ("radvd -C /etc/radvd/radvd.conf -m logfile -l /var/log/radvd.log",)
    _shutdown = ("pkill radvd",)
    _validate = ("pidof radvd",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        ''' Generate a RADVD router advertisement daemon config file
        using the network address of each interface.
        '''
        cfg = "# auto-generated by RADVD service (utility.py)\n"
        for ifc in node.netifs():
            if hasattr(ifc, 'control') and ifc.control == True:
                continue
            prefixes = list(map(cls.subnetentry, ifc.addrlist))
            if len(prefixes) < 1:
                continue
            cfg += """\
interface %s
{
        AdvSendAdvert on;
        MinRtrAdvInterval 3;
        MaxRtrAdvInterval 10;
        AdvDefaultPreference low;
        AdvHomeAgentFlag off;
""" % ifc.name
            for prefix in prefixes:
                if prefix == "":
                    continue
                cfg += """\
        prefix %s
        {
                AdvOnLink on;
                AdvAutonomous on;
                AdvRouterAddr on;
        };
""" % prefix
            cfg += "};\n"
        return cfg

    @staticmethod
    def subnetentry(x):
        ''' Generate a subnet declaration block given an IPv6 prefix string
            for inclusion in the RADVD config file.
        '''
        if x.find(":") >= 0:
            net = IPv6Prefix(x)
            return str(net)
        else:
            return ""

addservice(RadvdService)

class AtdService(UtilService):
    ''' Atd service for scheduling at jobs
    '''
    _name = "atd"
    _configs = ("startatd.sh",)
    _dirs = ("/var/spool/cron/atjobs", "/var/spool/cron/atspool")
    _startup = ("sh startatd.sh", )
    _shutdown = ("pkill atd", )

    @classmethod
    def generateconfig(cls, node, filename, services):
        return """
#!/bin/sh
echo 00001 > /var/spool/cron/atjobs/.SEQ
chown -R daemon /var/spool/cron/*
chmod -R 700 /var/spool/cron/*
atd
"""

addservice(AtdService)

class CronService(UtilService):
    _name = "Cron"
    _dirs = (('/etc', 'union'), ('/var/spool/cron', 'bind'), ('/run', 'bind'))
    _configs = ('/etc/crontab',)
    _startup = ("/usr/sbin/cron",)

    @classmethod
    def generateconfig(cls, node, filename, services):
        return """# /etc/crontab: system-wide crontab
# Unlike any other crontab you don't have to run the `crontab'
# command to install the new version when you edit this file
# and files in /etc/cron.d. These files also have username fields,
# that none of the other crontabs do.

SHELL=/bin/sh
PATH=/usr/local/sbin:/usr/local/bin:/sbin:/bin:/usr/sbin:/usr/bin

# deactivated hourly, daily, weekly, monthly cronjobs by default,
# as it unclear (as of network-configure-time) which files reside inside
# their respective directories
# m h dom mon dow user  command
#17 *    * * *   root    cd / && run-parts --report /etc/cron.hourly
#25 6    * * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.daily )
#47 6    * * 7   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.weekly )
#52 6    1 * *   root    test -x /usr/sbin/anacron || ( cd / && run-parts --report /etc/cron.monthly )
#
"""

addservice(CronService)

class UserDefinedService(UtilService):
    ''' Dummy service allowing customization of anything.
    '''
    _name = "UserDefined"
    _startindex = 50
    _meta = "Customize this service to do anything upon startup."

addservice(UserDefinedService)
