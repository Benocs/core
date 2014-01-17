# Autoconfiguring CORE Routing Services
# Copyright (C) 2014 Robert Wuttke <flash@jpod.cc>
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

''' auto-configuring BGP, OSPF services for multi-AS networks.
'''

import os

from core.service import CoreService, addservice
from core.services import quagga
from core.misc.ipaddr import IPv4Prefix, IPv6Prefix, isIPv4Address, isIPv6Address
from core.misc import ipaddress

from core.service import CoreService, addservice

class MBgp(quagga.Bgp):

	_name = "MBGP"

	"""
	CONFIGURING QUAGGA:
	node: <core.netns.nodes.CoreNode object at 0x7fd750040d50>,
		['__class__', '__delattr__', '__dict__', '__doc__', '__format__',
		'__getattribute__', '__hash__', '__init__', '__module__',
		'__new__', '__reduce__', '__reduce_ex__', '__repr__', '__setattr__',
		'__sizeof__', '__str__', '__subclasshook__', '__weakref__', '_mounts',
		'_netif', 'addaddr', 'addfile', 'addnetif', 'addservice', 'alive',
		'apitype', 'attachnet', 'boot', 'bootsh', 'canvas', 'cmd', 'cmdresult',
		'commonnets', 'connectnode', 'ctrlchnlname', 'deladdr', 'delalladdr',
		'delnetif', 'detachnet', 'exception', 'getaddr', 'getifindex',
		'getposition', 'hostfilename', 'icmd', 'icon', 'ifindex', 'ifname', 'ifup',
		'info', 'lock', 'makenodedir', 'mount', 'name', 'netif', 'netifs',
		'netifstats', 'newifindex', 'newnetif', 'newtuntap', 'newveth', 'nodedir',
		'nodefile', 'nodefilecopy', 'nodeid', 'numnetif', 'objid', 'opaque',
		'opennodefile', 'pid', 'popen', 'position', 'privatedir', 'redircmd',
		'rmnodedir', 'services', 'session', 'sethwaddr', 'setposition', 'shcmd',
		'shutdown', 'startup', 'term', 'termcmdstring', 'tmpnodedir', 'tolinkmsgs',
		'tonodemsg', 'type', 'umount', 'up', 'valid_deladdrtype', 'validate',
		'verbose', 'vnodeclient', 'warn']
	"""

	@classmethod
	def generatequaggaconfig(cls, node):

		cfg = "!\n! BGP configuration\n!\n"
		cfg += "router bgp %s\n" % node.netid
		cfg += "  bgp router-id %s\n" % cls.routerid(node)
		cfg += "  redistribute connected\n"
		cfg += "  redistribute ospf\n"
		cfg += "  redistribute isis\n"

		#cfg += "	redistribute system\n"
		#cfg += "	redistribute kernel\n"
		#cfg += "	redistribute connected\n"
		#cfg += "	redistribute static\n"
		#cfg += "	redistribute rip\n"
		#cfg += "	redistribute ripng\n"
		#cfg += "	redistribute ospf\n"
		#cfg += "	redistribute ospf6\n"
		#cfg += "	redistribute isis\n"
		#cfg += "	redistribute hsls\n"
		cfg += "!\n"
		# aggregate networks that are being used for internal transit and access
		# TODO: find a more generic way. this approach works well for
		# two-AS-networks. ideally, each network should only aggregate the address
		# space that it allocates to it's client or the space that is being used by
		# it's internal routers (i.e., IGP, non-EGP)
		cfg += "  aggregate-address 172.16.0.0 255.240.0.0 summary-only\n"
		cfg += "  aggregate-address 192.168.0.0 255.255.0.0 summary-only\n"
		# don't aggregate networks that are being used for inter-AS routing
		#cfg += "  aggregate-address 10.0.0.0 255.0.0.0 summary-only\n!\n"
		cfg += "!\n"

		# find any link on which two different netid's (i.e., AS numbers) are
		# present and configure a bgp-session between the two corresponding nodes.
		# on all other interfaces, disable bgp
		for localnetif in node.netifs():
			#print('\nnetif: %s ' % str(localnetif))
			#print('localnetif net: %s ' % str(localnetif.net))

			for idx, net_netif in localnetif.net._netif.items():
				#print('idx: %s, %s' % (str(idx), str(net_netif)))
				candidate_node = net_netif.node
				#print('candidate node: %s, netid: %s' % (str(candidate_node),
				#		str(candidate_node.netid)))

				# skip our own interface
				if localnetif == net_netif.node:
					continue

				# found at least two different ASes.
				if not node.netid == net_netif.node.netid:
					#print('found two different ASes: local: %s, remote: %s' %
					#		(str(node.netid), str(net_netif.node.netid)))

					# TODO: break after first link with this neighbor is established?
					for addr in net_netif.addrlist:
						(ip, sep, mask)  = addr.partition('/')
						#print('configuring BGP neighbor: %s' % str(ip))

						cfg += "  neighbor %s remote-as %s\n" % \
								(str(ip), str(net_netif.node.netid))

		return cfg

addservice(MBgp)

class MOspfv2(quagga.Ospfv2):

	_name = "MOSPFv2"

	@classmethod
	def generatequaggaconfig(cls, node):
		cfg = "!\n! OSPFv2 (for IPv4) configuration\n!\n"
		cfg += "router ospf\n"
		cfg += "  router-id %s\n" % cls.routerid(node)
		cfg += "  redistribute connected\n"
		cfg += "  redistribute bgp\n"
		cfg += "!\n"

		for ifc in node.netifs():
			if hasattr(ifc, 'control') and ifc.control == True:
				continue

			# find any link on which two equal netid's (i.e., AS numbers) are
			# present and configure an ospf-session on this interface
			# on all other interfaces, disable ospf
			for idx, net_netif in ifc.net._netif.items():

				# skip our own interface
				if ifc == net_netif:
					continue

				# found the same AS, enable IGP/OSPF
				if node.netid == net_netif.node.netid:
					for a in ifc.addrlist:
						if a.find(".") < 0:
							continue
						cfg += "  network %s area 0\n" % a
		cfg += "!\n"
		return cfg

addservice(MOspfv2)

class ISIS(quagga.QuaggaService):
	''' The user generated service isisd provides a ISIS
	'''
	_name = "ISIS"
	_startup = ("sh quaggaboot.sh isisd",)
	_shutdown = ("killall isisd", )
	_validate = ("pidof isisd", )

	@classmethod
	def generatequaggaifcconfig(cls,  node,  ifc):
		added_ifc = False

		cfg = ""

		# find any link on which two equal netid's (i.e., AS numbers) are
		# present and configure an isis-session on this interface
		# on all other interfaces, disable isis
		for idx, net_netif in ifc.net._netif.items():

			# only add each interface once
			if added_ifc:
				break

			# skip our own interface
			if ifc == net_netif:
				continue

			# found the same AS, enable IGP/ISIS
			if not added_ifc and node.netid == net_netif.node.netid:
				#cfg += "interface %s\n" % ifc.name
				cfg += "  ip router isis 1\n"
				cfg += "  isis circuit-type level-2-only\n"
				cfg += "!\n"
				# only add each interface once
				added_ifc = True

		return cfg

	@classmethod
	def generatequaggaconfig(cls, node):
		cfg = "!\n! ISIS configuration\n!\n"
		cfg += "log file /tmp/isis-%s.log debugging\n" % cls.routerid(node)
		cfg += "interface lo\n"
		cfg += "  ip router isis 1\n"
		cfg += "!\n"

		cfg += "router isis 1\n"
		# TODO	loesung aendern damit er nicht die ip vom ctrl netz nimmt...
		# TODO geht so nur wenn ipv4 adresse vorhanden
		#cfg += "  net 49.%s.00\n" % cls.bearbeiteipstr(cls.routerid(node))
		cfg += "  net %s\n" % cls.bearbeiteipstr(cls.routerid(node), str(node.netid))
		#cfg += " is-type level-2\n!\n"
		# TODO: redistribution of routes is not yet implemented in quagga
		#cfg += "  redistribute connected\n"
		#cfg += "  redistribute bgp\n"
		cfg += "!\n"


		return cfg

	@staticmethod
	def bearbeiteipstr(ipstr, netid):
		''' get ip return three middle blocks of isis netid
		'''
		"""
		# isis-is is 12 characters long
		# it has the format: 49.nnnn.aaaa.bbbb.cccc.00
		# where nnnn == netid (i.e., same on all routers)
		#       abc  == routerid (i.e., unique among all routers)

		hexip = hex(int(ipaddress.IPv4Address(ipstr)))[2:]
		if len(hexip) < 8:
			hexip = '0%s' % hexip

		netid = str(netid)
		isisnetidlist = [ '0' for i in range(4 - len(netid)) ]
		isisnetidlist.append(netid)
		isisnetid = ''.join(isisnetidlist)

		# 49.1000.
		#isisid = "49.%s.%s.%s.0000.00" % (isisnetid, hexip[:4], hexip[4:])
		isisid = "49.%s.%s.%s.0000.00" % (hexip[4:], hexip[:4], hexip[4:])
		#return isisid
		"""

		# punkte entfernen
		temp =	''.join(c for c in ipstr if c not in '.')
		# laenge auffuellen TODO schauen ob so immer richtig
		while len(temp) < 12:
			temp += str(12-len(temp))
		# punkte an richtiger stelle einfuegen und zurueckliefern
		return '49.' + temp[:4] + '.' + temp[4:8] + '.' + temp[8:] + '.00'

addservice(ISIS)

