#
# CORE
# Copyright (c)2011-2012 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# author: Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#
''' PhysicalNode class for including real systems in the emulated network.
'''
import os, threading, subprocess

from core.misc.ipaddr import *
from core.misc.utils import *
from core.constants import *
from core.api import coreapi
from core.coreobj import PyCoreNode, PyCoreNetIf
from core.emane.nodes import EmaneNode
if os.uname()[0] == "Linux":
    from core.netns.vnet import LxBrNet
    from core.netns.vif import GreTap
elif os.uname()[0] == "FreeBSD":
    from core.bsd.vnet import NetgraphNet


class PhysicalNode(PyCoreNode):
    def __init__(self, session, objid = None, name = None,
                 nodedir = None, verbose = False, start = True):
        PyCoreNode.__init__(self, session, objid, name, verbose=verbose,
                            start=start)
        self.nodedir = nodedir
        self.up = start
        self.lock = threading.RLock()
        self._mounts = []
        if start:
            self.startup()
        
    def boot(self):
        self.session.services.bootnodeservices(self)
        
    def validate(self):
        self.session.services.validatenodeservices(self)

    def startup(self):
        self.lock.acquire()
        try:
            self.makenodedir()
            #self.privatedir("/var/run")
            #self.privatedir("/var/log")
        except OSError as e:
            self.exception(coreapi.CORE_EXCP_LEVEL_ERROR,
                "PhysicalNode.startup()", e)
        finally:
            self.lock.release()

    def shutdown(self):
        if not self.up:
            return
        self.lock.acquire()
        while self._mounts:
            source, target, mount_type = self._mounts.pop(-1)
            self.umount(target)
        for netif in self.netifs():
            netif.shutdown()
        self.rmnodedir()
        self.lock.release()


    def termcmdstring(self, sh = "/bin/sh"):
        ''' The broker will add the appropriate SSH command to open a terminal
        on this physical node.
        '''
        return sh
        
    def cmd(self, args, wait = True):
        ''' run a command on the physical node
        '''
        os.chdir(self.nodedir)
        try:
            if wait:
                # os.spawnlp(os.P_WAIT, args)
                subprocess.call(args)
            else:
                # os.spawnlp(os.P_NOWAIT, args)
                subprocess.Popen(args)
        except CalledProcessError as e:
            self.warn("cmd exited with status %s: %s" % (e, str(args)))
        
    def cmdresult(self, args):
        ''' run a command on the physical node and get the result
        '''
        os.chdir(self.nodedir)
        # in Python 2.7 we can use subprocess.check_output() here
        tmp = subprocess.Popen(args, stdin = subprocess.PIPE,
                               stdout = subprocess.PIPE,
                               stderr = subprocess.PIPE)
        result = tmp.stdout.read().decode()
        result += tmp.stderr.read().decode()
        tmp.stdin.close()
        tmp.stdout.close()
        tmp.stderr.close()
        status = tmp.wait()
        return (status, result)
        
    def shcmd(self, cmdstr, sh = "/bin/sh"):
        return self.cmd([sh, "-c", cmdstr])

    def sethwaddr(self, ifindex, addr):
        ''' same as SimpleLxcNode.sethwaddr()
        '''
        self._netif[ifindex].sethwaddr(addr)
        ifname = self.ifname(ifindex)
        if self.up:
            (status, result) = self.cmdresult([IP_BIN, "link", "set", "dev",
                                              ifname, "address", str(addr)])
            if status:
                self.exception(coreapi.CORE_EXCP_LEVEL_ERROR,
                    "PhysicalNode.sethwaddr()",
                    "error setting MAC address %s" % str(addr))
                    
    def addaddr(self, ifindex, addr):
        ''' same as SimpleLxcNode.addaddr()
        '''
        if self.up:
            self.cmd([IP_BIN, "addr", "add", str(addr),
                  "dev", self.ifname(ifindex)])
        self._netif[ifindex].addaddr(addr)

    def deladdr(self, ifindex, addr):
        ''' same as SimpleLxcNode.deladdr()
        '''
        try:
            self._netif[ifindex].deladdr(addr)
        except ValueError:
            self.warn("trying to delete unknown address: %s" % addr)
        if self.up:
            self.cmd([IP_BIN, "addr", "del", str(addr),
                  "dev", self.ifname(ifindex)])

    def adoptnetif(self, netif, ifindex, hwaddr, addrlist):
        ''' The broker builds a GreTap tunnel device to this physical node.
        When a link message is received linking this node to another part of
        the emulation, no new interface is created; instead, adopt the
        GreTap netif as the node interface.
        '''
        netif.name = "gt%d" % ifindex
        netif.node = self
        self.addnetif(netif, ifindex)
        # use a more reasonable name, e.g. "gt0" instead of "gt.56286.150"
        if self.up:
            self.cmd([IP_BIN, "link", "set", "dev", netif.localname, "down"])
            self.cmd([IP_BIN, "link", "set", netif.localname, "name", netif.name])
        netif.localname = netif.name
        if hwaddr:
            self.sethwaddr(ifindex, hwaddr)
        for addr in maketuple(addrlist):
            self.addaddr(ifindex, addr)
        if self.up:
            self.cmd([IP_BIN, "link", "set", "dev", netif.localname, "up"])
            
    def linkconfig(self, netif, bw = None, delay = None,
                   loss = None, duplicate = None, jitter = None, netif2 = None):
        ''' Apply tc queing disciplines using LxBrNet.linkconfig()
        '''
        if os.uname()[0] == "Linux":
            netcls = LxBrNet
        elif os.uname()[0] == "FreeBSD":
            netcls = NetgraphNet
        else:
            raise NotImplementedError("unsupported platform")
        # borrow the tc qdisc commands from LxBrNet.linkconfig()
        tmp = netcls(session=self.session, start=False)
        tmp.up = True
        tmp.linkconfig(netif, bw=bw, delay=delay, loss=loss,
                       duplicate=duplicate, jitter=jitter, netif2=netif2)
        del tmp

    def newifindex(self):
        self.lock.acquire()
        try:
            while self.ifindex in self._netif:
                self.ifindex += 1
            ifindex = self.ifindex
            self.ifindex += 1
            return ifindex
        finally:
            self.lock.release()

    def newnetif(self, net = None, addrlist = [], hwaddr = None,
                 ifindex = None, ifname = None):
        if self.up and net is None:
            raise NotImplementedError
        if ifindex is None:
            ifindex = self.newifindex()

        if self.up:
            # this is reached when this node is linked to a network node
            # tunnel to net not built yet, so build it now and adopt it
            gt = self.session.broker.addnettunnel(net.objid)
            if gt is None or len(gt) != 1:
                self.session.warn("Error building tunnel from PhysicalNode."
                                  "newnetif()")
            gt = gt[0]
            net.detach(gt)
            self.adoptnetif(gt, ifindex, hwaddr, addrlist)
            return ifindex
            
        # this is reached when configuring services (self.up=False)
        if ifname is None:
            ifname = "gt%d" % ifindex
        netif = GreTap(node = self, name = ifname, session = self.session,
                       start = False)
        self.adoptnetif(netif, ifindex, hwaddr, addrlist)
        return ifindex

    def privatedir(self, path, mount_type = None):
        if path[0] != "/":
            raise ValueError("path not fully qualified: " + path)
        hostpath = os.path.join(self.nodedir, path[1:].replace("/", "."))
        try:
            os.mkdir(hostpath)
        except OSError:
            pass
        except Exception as e:
            raise Exception(e)
        self.mount(hostpath, path, mount_type)

    def mount(self, source, target, mount_type = None):
        self.info('received mount request. type: %s, source, target: %s -> %s' % (str(mount_type),
                source, target))

        # we only mount top-level directories. strip any sub-dirs from paths
        self.info('orig source, target: %s -> %s' % (source, target))
        if target.count('/') > 1:
            source = source[:source.find(target)]
            target = target[:target[1:].find('/')+1]
            source = os.path.join(source, target[1:])
        self.info('new  source, target: %s -> %s' % (source, target))

        #for mount in self._mounts.append((source, target, mount_type))
        already_mounted = False
        for s, t, mt in self._mounts:
            if target == t:
                if mt == mount_type or \
                        (mount_type is None and mt == getDefaultMountType(target)):
                    already_mounted = True
                    break
                elif mt == 'bind':
                    self.warn('mt: %s, mount_type: %s, default: %s' % (str(mt), str(mount_type),
                            str(getDefaultMountType(target))))
                    self.info(('mount type collision on directory: "%s".\n'
                            '  the same directory is being requested with '
                            'different mount types while already being mounted using '
                            'bind-mounts.  remounting using union-mount...') % target)
                    self.umount(target)
                    already_mounted = False
                    break

        if already_mounted:
            self.info('directory %s already mounted.' % target)
            return

        source = os.path.abspath(source)
        self.info("nodedir: %s" % self.nodedir)
        if mount_type is None:
            mount_type = getDefaultMountType(target)
            self.info('mounting %s at %s using %s-mounts' % (source, target, mount_type))
        else:
            if mount_type == 'bind':
                self.info('mounting %s at %s using bind-mounts' % (source, target))
            elif mount_type == 'union':
                self.info('mounting %s at %s using union-mounts' % (source, target))
            else:
                mount_type = getDefaultMountType(target)
                self.info('mounting %s at %s using %s-mounts' % (source, target, mount_type))

        try:
            if mount_type == 'bind':
                shcmd = "mkdir -p '%s' && %s -n --bind '%s' '%s'" % \
                    (target, MOUNT_BIN, source, target)
                self.info('assembled bindcmd: %s' % shcmd)
            elif mount_type == 'union':
                host_dirs = os.path.join(self.nodedir, '../host_dirs')
                self.info('host_dirs: %s' % host_dirs)

                bound_host_dir = os.path.join(host_dirs, target.lstrip('/'))
                self.info('bound_host_dir: %s' % bound_host_dir)

                shcmditems = []
                shcmditems.append("mkdir -p '%s' && mkdir -p '%s' && " %
                        (bound_host_dir, target))
                if not os.path.exists(bound_host_dir):
                    shcmditems.append("rsync -avhP '%s/' '%s/' && " %
                            (target, bound_host_dir))
                shcmditems.extend([("%s -o cow,max_files=32768 "
                        "-o allow_other,use_ino,suid,dev,nonempty "
                        "%s=RW:%s=RO %s") % (UNIONFS_BIN, source,
                        bound_host_dir, target)])
                shcmd = ''.join(shcmditems)
                self.info('assembled unionfscmd: %s' % shcmd)
            else:
                raise ValueError
            self.shcmd(shcmd)
            if mount_type == 'union':
                self._mounts.append((target, bound_host_dir, mount_type))
            self._mounts.append((source, target, mount_type))
        except Exception as e:
            self.warn("mounting failed for %s at %s. reason: %s" % (source, target, e))

    def umount(self, target):
        self.info("unmounting '%s'" % target)
        try:
            self.cmd([UMOUNT_BIN, "-l", target])
        except:
            self.warn("unmounting failed for %s" % target)

    def opennodefile(self, filename, mode = "w"):
        dirname, basename = os.path.split(filename)
        if not basename:
            raise ValueError("no basename for filename: " + filename)
        if dirname and dirname[0] == "/":
            dirname = dirname[1:]
        dirname = dirname.replace("/", ".")
        dirname = os.path.join(self.nodedir, dirname)
        if not os.path.isdir(dirname):
            os.makedirs(dirname, mode = 0o755)
        hostfilename = os.path.join(dirname, basename)
        return open(hostfilename, mode)

    def nodefile(self, filename, contents, mode = 0o644):
        f = self.opennodefile(filename, "w")
        f.write(contents)
        os.chmod(f.name, mode)
        f.close()
        self.info("created nodefile: '%s'; mode: 0%o" % (f.name, mode))

    def chmod(self, filename, mode = 0o644):
        if os.path.exists(filename):
            os.chmod(filename, mode)
