#
# CORE
# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# authors: Tom Goff <thomas.goff@boeing.com>
#          Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
# Copyright (C) 2014 Robert Wuttke <robert@benocs.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

'''
vnode.py: PyCoreNode and LxcNode classes that implement the network namespace
virtual node.
'''

import os, signal, sys, subprocess, threading, string, shutil
import random, time
from core.api import coreapi
from core.misc.utils import *
from core.constants import *
from core.coreobj import PyCoreObj, PyCoreNode, PyCoreNetIf, Position
from core.netns.vif import VEth, TunTap
from core.netns import vnodeclient
from core.emane.nodes import EmaneNode

checkexec([IP_BIN])

class SimpleLxcNode(PyCoreNode):
    def __init__(self, session, objid = None, name = None, nodedir = None,
                 verbose = False, start = True):
        PyCoreNode.__init__(self, session, objid, name, verbose=verbose,
                            start=start)
        self.nodedir = nodedir
        self.ctrlchnlname = \
            os.path.abspath(os.path.join(self.session.sessiondir, self.name))
        self.vnodeclient = None
        self.pid = None
        self.up = False
        self.lock = threading.RLock()
        self._mounts = []

    def alive(self):
        try:
            os.kill(self.pid, 0)
        except OSError:
            return False
        return True

    def startup(self):
        ''' Start a new namespace node by invoking the vnoded process that
            allocates a new namespace. Bring up the loopback device and set
            the hostname.
        '''
        if self.up:
            raise Exception("already up")
        vnoded = ["%s/vnoded" % CORE_SBIN_DIR, "-v", "-c", self.ctrlchnlname,
                  "-l", self.ctrlchnlname + ".log",
                  "-p", self.ctrlchnlname + ".pid"]
        if self.nodedir:
            vnoded += ["-C", self.nodedir]
        env = self.session.getenviron(state=False)
        env['NODE_NUMBER'] = str(self.objid)
        env['NODE_NAME'] = str(self.name)
        try:
            tmp = subprocess.Popen(vnoded, stdout = subprocess.PIPE, env = env)
        except OSError as e:
            msg = "error running vnoded command: %s (%s)" % (vnoded, e)
            self.exception(coreapi.CORE_EXCP_LEVEL_FATAL,
                "SimpleLxcNode.startup()", msg)
            raise Exception(msg)
        try:
            self.pid = int(tmp.stdout.read().decode())
            tmp.stdout.close()
        except Exception:
            msg = "vnoded failed to create a namespace; "
            msg += "check kernel support and user priveleges"
            self.exception(coreapi.CORE_EXCP_LEVEL_FATAL,
                           "SimpleLxcNode.startup()", msg)
        if tmp.wait():
            raise Exception("command failed: %s" % vnoded)
        self.vnodeclient = vnodeclient.VnodeClient(self.name,
                                                   self.ctrlchnlname)
        self.info("bringing up loopback interface")
        self.cmd([IP_BIN, "link", "set", "lo", "up"])
        self.info("adding IPv4 loopback address: %s/32" % \
                str(self.getLoopbackIPv4()))
        self.cmd([IP_BIN, "addr", "add", "%s/32" % str(self.getLoopbackIPv4()),
                "dev", "lo"])
        self.info("adding IPv6 loopback address: %s/128" % \
                str(self.getLoopbackIPv6()))
        self.cmd([IP_BIN, "addr", "add", "%s/128" % str(self.getLoopbackIPv6()),
                "dev", "lo"])
        self.info("setting hostname: %s" % self.name)
        self.cmd(["hostname", self.name])
        self.up = True

    def shutdown(self):
        if not self.up:
            return
        while self._mounts:
            source, target, mount_type = self._mounts.pop(-1)
            self.umount(target)
        #print "XXX del vnodeclient:", self.vnodeclient
        # XXX XXX XXX this causes a serious crash
        #del self.vnodeclient
        for netif in self.netifs():
            netif.shutdown()
        try:
            os.kill(self.pid, signal.SIGTERM)
            os.waitpid(self.pid, 0)
        except OSError:
            pass
        try:
            os.unlink(self.ctrlchnlname)
        except OSError:
            pass
        self._netif.clear()
        #del self.session
        # print "XXX del vnodeclient:", self.vnodeclient
        del self.vnodeclient
        self.up = False

    def cmd(self, args, wait = True):
        return self.vnodeclient.cmd(args, wait)

    def cmdresult(self, args):
        return self.vnodeclient.cmdresult(args)

    def popen(self, args):
        return self.vnodeclient.popen(args)

    def icmd(self, args):
        return self.vnodeclient.icmd(args)

    def redircmd(self, infd, outfd, errfd, args, wait = True):
        return self.vnodeclient.redircmd(infd, outfd, errfd, args, wait)

    def term(self, sh = "/bin/sh"):
        return self.vnodeclient.term(sh = sh)

    def termcmdstring(self, sh = "/bin/sh"):
        return self.vnodeclient.termcmdstring(sh = sh)

    def shcmd(self, cmdstr, sh = "/bin/sh"):
        return self.vnodeclient.shcmd(cmdstr, sh = sh)

    def boot(self):
        pass

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

        ### tmp. mv to config ###
        def getDefaultMountType(target):
            defaultmounts = {
                # fallback to default if no specified directory matches
                '*': 'union',
                '/bin': 'union',
                '/boot': 'union',
                # TODO: introduce third mount-type for dev, proc, et al?
                '/dev': 'bind',
                '/etc': 'union',
                '/home': 'bind',
                '/lib': 'union',
                '/lib64': 'union',
                '/media': 'bind',
                '/mnt': 'bind',
                # TODO: opt: bind or union
                '/opt': 'bind',
                # TODO: introduce third mount-type for dev, proc, et al?
                '/proc': 'bind',
                '/root': 'bind',
                '/run': 'bind',
                '/sbin': 'union',
                '/srv': 'bind',
                # TODO: introduce third mount-type for dev, proc, et al?
                '/sys': 'bind',
                '/tmp': 'bind',
                '/usr': 'union',
                '/var': 'bind'
                }

            mount_type = None
            for key in list(defaultmounts.keys()):
                if target.startswith(key):
                    mount_type = defaultmounts[key]
                    break
            if mount_type is None:
                mount_type = defaultmounts['*']

            return mount_type
        ### /tmp ###

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
            self.cmd([UMOUNT_BIN, "-n", "-l", target])
        except:
            self.warn("unmounting failed for %s" % target)

    def newifindex(self):
        with self.lock:
            return PyCoreNode.newifindex(self)

    def newveth(self, ifindex = None, ifname = None, net = None):
        self.lock.acquire()
        try:
            if ifindex is None:
                ifindex = self.newifindex()
            if ifname is None:
                ifname = "eth%d" % ifindex
            sessionid = self.session.shortsessionid()
            name = "n%s.%s.%s" % (self.objid, ifindex, sessionid)
            localname = "n%s.%s.%s" % (self.objid, ifname, sessionid)
            if len(ifname) > 16:
                raise ValueError("interface local name '%s' to long" % \
                        localname)
            ifclass = VEth
            veth = ifclass(node = self, name = name, localname = localname,
                           mtu = 1500, net = net, start = self.up)
            if self.up:
                check_call([IP_BIN, "link", "set", veth.name,
                            "netns", str(self.pid)])
                self.cmd([IP_BIN, "link", "set", veth.name, "name", ifname])
            veth.name = ifname
            try:
                self.addnetif(veth, ifindex)
            except:
                veth.shutdown()
                del veth
                raise
            return ifindex
        finally:
            self.lock.release()

    def newtuntap(self, ifindex = None, ifname = None, net = None):
        self.lock.acquire()
        try:
            if ifindex is None:
                ifindex = self.newifindex()
            if ifname is None:
                ifname = "eth%d" % ifindex
            sessionid = self.session.shortsessionid()
            localname = "n%s.%s.%s" % (self.objid, ifindex, sessionid)
            name = ifname
            ifclass = TunTap
            tuntap = ifclass(node = self, name = name, localname = localname,
                             mtu = 1500, net = net, start = self.up)
            try:
                self.addnetif(tuntap, ifindex)
            except:
                tuntap.shutdown()
                del tuntap
                raise
            return ifindex
        finally:
            self.lock.release()

    def sethwaddr(self, ifindex, addr):
        self._netif[ifindex].sethwaddr(addr)
        if self.up:
            (status, result) = self.cmdresult([IP_BIN, "link", "set", "dev",
                                    self.ifname(ifindex), "address", str(addr)])
            if status:
                self.exception(coreapi.CORE_EXCP_LEVEL_ERROR,
                    "SimpleLxcNode.sethwaddr()",
                    "error setting MAC address %s" % str(addr))
    def addaddr(self, ifindex, addr):
        if self.up:
            self.cmd([IP_BIN, "addr", "add", str(addr),
                  "dev", self.ifname(ifindex)])
        self._netif[ifindex].addaddr(addr)

    def deladdr(self, ifindex, addr):
        try:
            self._netif[ifindex].deladdr(addr)
        except ValueError:
            self.warn("trying to delete unknown address: %s" % addr)
        if self.up:
            self.cmd([IP_BIN, "addr", "del", str(addr),
                  "dev", self.ifname(ifindex)])

    valid_deladdrtype = ("inet", "inet6", "inet6link")
    def delalladdr(self, ifindex, addrtypes = valid_deladdrtype):
        addr = self.getaddr(self.ifname(ifindex), rescan = True)
        for t in addrtypes:
            if t not in self.valid_deladdrtype:
                raise ValueError("addr type must be in: " + \
                    " ".join(self.valid_deladdrtype))
            for a in addr[t]:
                self.deladdr(ifindex, a)
        # update cached information
        self.getaddr(self.ifname(ifindex), rescan = True)

    def ifup(self, ifindex):
        if self.up:
            self.cmd([IP_BIN, "link", "set", self.ifname(ifindex), "up"])

    def newnetif(self, net = None, addrlist = [], hwaddr = None,
                 ifindex = None, ifname = None):
        self.lock.acquire()
        try:
            if isinstance(net, EmaneNode):
                ifindex = self.newtuntap(ifindex = ifindex, ifname = ifname,
                                         net = net)
                # TUN/TAP is not ready for addressing yet; the device may
                #   take some time to appear, and installing it into a
                #   namespace after it has been bound removes addressing;
                #   save addresses with the interface now
                self.attachnet(ifindex, net)
                netif = self.netif(ifindex)
                netif.sethwaddr(hwaddr)
                for addr in maketuple(addrlist):
                    netif.addaddr(addr)
                return ifindex
            else:
                ifindex = self.newveth(ifindex = ifindex, ifname = ifname,
                                       net = net)
            if net is not None:
                self.attachnet(ifindex, net)
            if hwaddr:
                self.sethwaddr(ifindex, hwaddr)
            for addr in maketuple(addrlist):
                self.addaddr(ifindex, addr)
            self.ifup(ifindex)
            return ifindex
        finally:
            self.lock.release()

    def connectnode(self, ifname, othernode, otherifname):
        tmplen = 8
        tmp1 = "tmp." + "".join([random.choice(string.ascii_lowercase)
                                 for x in range(tmplen)])
        tmp2 = "tmp." + "".join([random.choice(string.ascii_lowercase)
                                 for x in range(tmplen)])
        check_call([IP_BIN, "link", "add", "name", tmp1,
                    "type", "veth", "peer", "name", tmp2])

        check_call([IP_BIN, "link", "set", tmp1, "netns", str(self.pid)])
        self.cmd([IP_BIN, "link", "set", tmp1, "name", ifname])
        self.addnetif(PyCoreNetIf(self, ifname), self.newifindex())

        check_call([IP_BIN, "link", "set", tmp2, "netns", str(othernode.pid)])
        othernode.cmd([IP_BIN, "link", "set", tmp2, "name", otherifname])
        othernode.addnetif(PyCoreNetIf(othernode, otherifname),
                           othernode.newifindex())

    def addfile(self, srcname, filename):
        shcmd = "mkdir -p $(dirname '%s') && mv '%s' '%s' && sync" % \
            (filename, srcname, filename)
        self.shcmd(shcmd)

    def getaddr(self, ifname, rescan = False):
        return self.vnodeclient.getaddr(ifname = ifname, rescan = rescan)

    def netifstats(self, ifname = None):
        return self.vnodeclient.netifstats(ifname = ifname)


class LxcNode(SimpleLxcNode):
    def __init__(self, session, objid = None, name = None,
                 nodedir = None, bootsh = "boot.sh", verbose = False,
                 start = True):
        super(LxcNode, self).__init__(session = session, objid = objid,
                                      name = name, nodedir = nodedir,
                                      verbose = verbose, start = start)
        self.bootsh = bootsh
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
            super(LxcNode, self).startup()
            self.privatedir("/var/run")
            self.privatedir("/var/log")
        except OSError as e:
            self.warn("Error with LxcNode.startup(): %s" % e)
            self.exception(coreapi.CORE_EXCP_LEVEL_ERROR,
                "LxcNode.startup()", "%s" % e)
        finally:
            self.lock.release()

    def shutdown(self):
        if not self.up:
            return
        self.lock.acquire()
        # services are instead stopped when session enters datacollect state
        #self.session.services.stopnodeservices(self)
        try:
            super(LxcNode, self).shutdown()
        finally:
            self.rmnodedir()
            self.lock.release()

    def privatedir(self, path, mount_type = None):
        if not os.path.isabs(path):
            raise ValueError("path not fully qualified: " + path)
        #hostpath = os.path.join(self.nodedir, path[1:].replace("/", "."))
        hostpath = os.path.join(self.nodedir, path.lstrip('/'))
        try:
            os.makedirs(hostpath, exist_ok = True)
            #os.mkdir(hostpath)
        except OSError:
            pass
        except Exception as e:
            raise Exception(e)
        self.mount(hostpath, path, mount_type)

    def hostfilename(self, filename):
        ''' Return the name of a node's file on the host filesystem.
        '''
        dirname, basename = os.path.split(filename)
        if not basename:
            raise ValueError("no basename for filename: " + filename)
        if dirname and os.path.isabs(dirname):
            dirname = dirname.lstrip('/')
        #dirname = dirname.replace("/", ".")
        dirname = os.path.join(self.nodedir, dirname)
        return os.path.join(dirname, basename)

    def opennodefile(self, filename, mode = "w"):
        hostfilename = self.hostfilename(filename)
        dirname, basename = os.path.split(hostfilename)
        if not os.path.isdir(dirname):
            os.makedirs(dirname, mode = 0o755)
        return open(hostfilename, mode)

    def nodefile(self, filename, contents, mode = 0o644):
        f = self.opennodefile(filename, "w")
        f.write(contents)
        os.chmod(f.name, mode)
        f.close()
        self.info("created nodefile: '%s'; mode: 0%o" % (f.name, mode))

    def chmod(self, filename, mode = 0o644):
        filename = self.hostfilename(filename)
        if os.path.exists(filename):
            print(("chmodding file: %s to mode: 0%o" % (f.name, mode)))
            os.chmod(filename, mode)

    def nodefilecopy(self, filename, srcfilename, mode = None):
        ''' Copy a file to a node, following symlinks and preserving metadata.
        Change file mode if specified.
        '''
        hostfilename = self.hostfilename(filename)
        shutil.copy2(srcfilename, hostfilename)
        if mode is not None:
            os.chmod(hostfilename, mode)
        self.info("copied nodefile: '%s'; mode: %s" % (hostfilename, mode))

    def nodefilelink(self, srcfilename, filename, hard = True):
        ''' Create a link within the node to point to a file '''

        print(('nodefilelink: srcfilename: %s, filename: %s, hard: %s' % (str(srcfilename),
                str(filename), str(hard))))
        hostfilename = self.hostfilename(filename)
        print(('  hostfilename: %s' % (str(hostfilename))))
        if hard:
            os.link(srcfilename, hostfilename)
        else:
            os.symlink(srcfilename, hostfilename)
        self.info("created link : '%s' -> '%s'" % (srcfilename, hostfilename))

