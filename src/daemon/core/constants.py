# Constants created by autoconf ./configure script
COREDPY_VERSION		= "4.6"
CORE_STATE_DIR		= "/var"
CORE_CONF_DIR		= "/etc/core"
CORE_DATA_DIR		= "/usr/share/core"
CORE_LIB_DIR		= "/usr/lib/core"
CORE_SBIN_DIR		= "/usr/sbin"

BRCTL_BIN               = "/sbin/brctl"
SYSCTL_BIN              = "/sbin/sysctl"
IP_BIN                  = "/sbin/ip"
TC_BIN                  = "/sbin/tc"
EBTABLES_BIN            = "/sbin/ebtables"
IFCONFIG_BIN            = "/sbin/ifconfig"
NGCTL_BIN               = "no/ngctl"
VIMAGE_BIN              = "no/vimage"
QUAGGA_STATE_DIR        = "/var/run/quagga"
MOUNT_BIN               = "/bin/mount"
UMOUNT_BIN              = "/bin/umount"
UNIONFS_BIN             = "/usr/bin/unionfs-fuse"

config_files = ['ipaddrs.conf']

CONFIGS = {}
from os.path import exists, expanduser, join
# since this is the core-daemon, user should always expand to /root/
home = expanduser('~')
dotcore = join(home, '.core')
for configfile in config_files:
    fullpath = join(dotcore, configfile)
    configname = configfile[:configfile.rfind('.conf')]
    if exists(fullpath):
        localconfig = {}
        with open(fullpath, 'r') as f:
            for line in f:
                try:
                    key_value = line.split('=')
                    if not len(key_value) == 2:
                        print('ERROR: could not read line: %s' % line)
                        continue

                    key = key_value[0].replace('"', '').replace("'", "").strip()
                    value = key_value[1].replace('"', '').replace("'", "").strip()

                    print('new config: %s, %s = %s' % (configname, key, value))
                    localconfig[key] = value
                except:
                    print('ERROR: could not read line: %s' % line)
        if len(localconfig) > 0:
            CONFIGS[configname] = localconfig

