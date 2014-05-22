#
# Copyright 2005-2013 the Boeing Company.
# See the LICENSE file included in this distribution.
#

#
# Copyright 2005-2008 University of Zagreb, Croatia.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY AUTHOR AND CONTRIBUTORS ``AS IS'' AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL AUTHOR OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
# HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
# OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
# SUCH DAMAGE.
#
# This work was supported in part by Croatian Ministry of Science
# and Technology through the research contract #IP-2003-143.
#

#****h* imunes/ipv4.tcl
# NAME
#   ipv4.tcl -- file for handeling IPv4
#****

#****f* ipv4.tcl/findFreeIPv4Net
# NAME
#   findFreeIPv4Net -- find free IPv4 network
# SYNOPSIS
#   set ipnet [findFreeIPv4Net $mask]
# FUNCTION
#   Finds a free IPv4 network. Network is concidered to be free
#   if there are no simulated nodes attached to it. 
# INPUTS
#   * mask -- this parameter is left unused for now
# RESULT
#   * ipnet -- returns the free IPv4 network address in the form 10.a.b 
#****
#global tempAS 

proc findFreeIPv4Net { quarknode mask } {

    # vergabe der 30er

    global g_prefs node_list tempAS 

    set ipnets5 {}

    #testweise so, spaeter optimieren
    # alle ips byte 0-4 -> zB 10.14.54.2/30 -> 10 14 54 2 30
    foreach node $node_list {
        foreach ifc [ifcList $node] {
            set ipnet5 [lrange [split [getIfcIPv4addr $node $ifc] "./"] 0 4]
            if {[lsearch $ipnets5 $ipnet5] == -1} {
                lappend ipnets5 $ipnet5
            }
        }
    }

    # alle neuen ips byte 0-3
    # include mobility newlinks in search
    foreach newlink [.c find withtag "newlink"] {
        set ipnet5 [lrange [split [lindex [.c gettags $newlink] 4] "./"] 0 4]
        lappend ipnets5 $ipnet5
    }



    set ipnets4 {}

    # alle ips byte 0-3 -> zB 10.14.54.2 -> 10 14 54 2 
    foreach node $node_list {
	foreach ifc [ifcList $node] {
	    set ipnet4 [lrange [split [getIfcIPv4addr $node $ifc] "./"] 0 3]
	    if {[lsearch $ipnets4 $ipnet4] == -1} {
		lappend ipnets4 $ipnet4
	    }
	}
    }

    # alle neuen ips byte 0-3
    # include mobility newlinks in search
    foreach newlink [.c find withtag "newlink"] {
        set ipnet4 [lrange [split [lindex [.c gettags $newlink] 4] "./"] 0 3]
	lappend ipnets4 $ipnet4
    }




    set ipnets3 {}

    # alle ips byte 0-2 -> zB 10.14.54 -> 10 14 54 
    foreach node $node_list {
        foreach ifc [ifcList $node] {
            set ipnet3 [lrange [split [getIfcIPv4addr $node $ifc] .] 0 2]
            if {[lsearch $ipnets3 $ipnet3] == -1} {
                lappend ipnets3 $ipnet3
            }
        }
    }

    # alle neuen ips byte 0-3
    # include mobility newlinks in search
    foreach newlink [.c find withtag "newlink"] {
        set ipnet3 [lrange [split [lindex [.c gettags $newlink] 4] .] 0 2]
        lappend ipnets3 $ipnet3
    }


    # die addresse dann byte 0-3
    if {![info exists g_prefs(gui_ipv4_addr)]} { setDefaultAddrs ipv4 }
    set abcd [split $g_prefs(gui_ipv4_addr) .]


    set a [lindex $abcd 0] 
    set b [lindex $abcd 1]
    set c [lindex $abcd 2]
    set d [lindex $abcd 3]

    #proc fuer asID
    set i [getASiD $quarknode]
	# von zu ASip abhandeln
	 if { [info exists tempAS] } {
		if { $tempAS != 999 } {
			set i $tempAS
		}
	}

	#  
	#  30er muessen immer vierer bloecke am stueck nehmen
	#   zB  0 <1 2> 3   4 <5 6> 7   8 <9 10> 11   12 <13 14> 15   16 <17 18> 19   20 <21 22> 23
	#   zB 6 und 9 fuer node ips darf bei 30er nicht vorkommen..
	# wenn geht logik vereinfachen	
	# testen ob 3. byte als 24er vergeben -> wenn ja incr j
        for { set j $c } { $j < 255 } { incr j } {
		if {[lsearch $ipnets3 "$a $i $j"] != -1} {
			# wenn vergeben -> testen ob 24 er
			if {[lsearch $ipnets5 "$a $i $j 1 24"] != -1} {
				# 1 er ip im 24 vorhanden -> netz vorhanden
				continue
			}
		}

	  	for { set lastByte $d } { $lastByte < 255 } { incr lastByte } {
	    		if {fmod([expr $lastByte],4) == 0} {
		 		incr lastByte 1
			} elseif {fmod([expr $lastByte],4) == 1 &&\
			 [lsearch $ipnets4 "$a $i $j $lastByte"] != -1} {
				incr lastByte 4
			} elseif {fmod([expr $lastByte],4) == 2 &&\
			 [lsearch $ipnets4 "$a $i $j $lastByte"] != -1} {
		 		incr lastByte 3
			} elseif {fmod([expr $lastByte],4) == 3} {
	 	 	 	incr lastByte 2
			} else { } 

			# abbruch wenn hinterstes byte zu groß
                        if { $lastByte > 254 } { continue }

	            	if {[lsearch $ipnets4 "$a $i $j $lastByte"] == -1} {
	                	set ipnet "$a.$i.$j.$lastByte"
	                	return $ipnet
            		} else {
			  #ip schon vorhanden - nichts unternehmen
			}
	  	}
        }
    
}


# asID wird zurueckgeliefert wenn nicht gesetzt 0
proc getASiD { nodeGetAS } {

       global g_prefs

       set asID [getNodeNetId $nodeGetAS]

       # groesser 255 wird in 0 umgewandelt
       # bei verwendung von topogen hat asID wert ""
       #  -> in prefs.conf definierter
       #  wert gui_asid_standard wird verwendet

       if { $asID == "" } {
         set asID $g_prefs(gui_asid_standard)
       }

       if { $asID > 255 } {
            	set asID "0"
       }

       return $asID
}


proc findFreeIPv4NetLink { linkNode mask ip4AmSwitchNetzAddressen } {

    #momentan vergabe der 24er

    global g_prefs node_list tempAS


    # effizienter machen wenn so funktional
    set ipnets4 {}
    # hier variablen zum test aller vier bytes vorhandener ips
    # alle ips byte 0-3
    foreach node $node_list {
	foreach ifc [ifcList $node] {
	    set ipnet4 [lrange [split [getIfcIPv4addr $node $ifc] "./"] 0 3]
	    if {[lsearch $ipnets4 $ipnet4] == -1} {
		lappend ipnets4 $ipnet4
	    }
	}
    }

    # alle neuen ips byte 0-3
    # include mobility newlinks in search
    foreach newlink [.c find withtag "newlink"] {
        set ipnet4 [lrange [split [lindex [.c gettags $newlink] 4] "./"] 0 3]
	lappend ipnets4 $ipnet4
    }


	# hier variablen zum test aller dreibytes vorhandener ips
    set ipnets3 {}
    # alle ips byte 0-2
    foreach node $node_list {
        foreach ifc [ifcList $node] {
            set ipnet3 [lrange [split [getIfcIPv4addr $node $ifc] .] 0 2]
            if {[lsearch $ipnets3 $ipnet3] == -1} {
                lappend ipnets3 $ipnet3
            }
        }
    }

    # alle neuen ips byte 0-2
    # include mobility newlinks in search
    foreach newlink [.c find withtag "newlink"] {
        set ipnet3 [lrange [split [lindex [.c gettags $newlink] 4] .] 0 2]
        lappend ipnets3 $ipnet3
    }


	# TODO megadoof
	set ipnets5 {}
        # hier variablen zum test aller vier bytes vorhandener ips
    # alle ips byte 0-3
    foreach node $node_list {
        foreach ifc [ifcList $node] {
            set ipnet5 [lrange [split [getIfcIPv4addr $node $ifc] "./"] 0 4]
            if {[lsearch $ipnets5 $ipnet5] == -1} {
                lappend ipnets5 $ipnet5
            }
        }
    }

    # alle neuen ips byte 0-3
    # include mobility newlinks in search
    foreach newlink [.c find withtag "newlink"] {
        set ipnet5 [lrange [split [lindex [.c gettags $newlink] 4] "./"] 0 4]
        lappend ipnets5 $ipnet5
    }



    # die addresse dann byte 0-3
    if {![info exists g_prefs(gui_ipv4_addr)]} { setDefaultAddrs ipv4 }
    set abcd [split $g_prefs(gui_ipv4_addr) .]


    set a [lindex $abcd 0]
    set b [lindex $abcd 1]
    set c [lindex $abcd 2]
    set d [lindex $abcd 3]


    # neu test auf 30er netmask mit asID
    #proc fuer asID
    set i [getASiD $linkNode] 


# TODO 24er muessen auch adressbereich der 30 beachten (immer 4er schritte von 0 an)
#   und nicht die selben adressen nehmen

	#puts "ip4AmSwitchNetzAddressen"
	#foreach ip4 $ip4AmSwitchNetzAddressen {
	#	puts $ip4
	#}

	# testen ob switch peerlist leer -> wenn ja neues netz aufmachen	
	if { 0 == [llength $ip4AmSwitchNetzAddressen] } {
	 	#fall neues 24er
        	for { set j $c } { $j <= 255 } { incr j } {

        	    if {[lsearch $ipnets3 "$a $i $j"] == -1} {
        	        set ipnet3 "$a.$i.$j.1"
        	        return $ipnet3
        	    }
        	}
	} else {
	 	#fall bestehendes 24er von peers uebernehmen und hochzaehlen
		set peers {}
	        foreach peerIP $ip4AmSwitchNetzAddressen {
		   
	            	set ippeer [lrange [split $peerIP .] 0 3]

	    		if {[lsearch $peers $ippeer] == -1} {
				lappend peers $ippeer
	    		}
	        }

		# setze c als 3. byteblock von der
		#   letzten ip der peers..) 
		#set c [lrange [lrange $peers 0 0] 0 0]
		set c [lindex [lindex $peers end] 2]

		#puts "i vorher"
		#puts $i

		# setze i als 2. byteblock unabhaengig von momentaner ASid
		#   anhand der letzten ip der peers am switch
		set i [lindex [lindex $peers end] 1]

		#puts "i nacher"
		#puts $i

		# wenn 255 erreicht -> fehler! 
		for { set k 1 } { $k <= 255 } { incr k } {
			
			if { $k == 255 } { puts "WARNING: switch 24er voll!" }
			 # hier verhindern dass net oder broadcast ips in verwendung
		  	 #  benutzt werden (effektiv nur broadcast verhindern, wenn
			 #  eine darunter verwendet wird im 30er ..)
			 if { fmod([expr $k + 1],4) == 0 &&\
				 [lsearch $ipnets5 "$a $i $c [expr $k - 1] 30"] != -1 } {
				 incr k 1
			 }
	        	 if {[lsearch $peers "$a $i $c $k"] == -1 &&\
				 [lsearch $ipnets4 "$a $i $c $k"] == -1 &&\
				  [lsearch $ipnets4 "$a $i $c [expr $k + 1]"] == -1 } {
		        	    set ipnet4 "$a.$i.$c.$k"
				    return $ipnet4
	        	 }
		}
	}

}


#****f* ipv4.tcl/autoIPv4addr 
# NAME
#   autoIPv4addr -- automaticaly assign an IPv4 address
# SYNOPSIS
#   autoIPv4addr $node $iface 
# FUNCTION
#   automaticaly assignes an IPv4 address to the interface $iface of 
#   of the node $node  
# INPUTS
#   * node -- the node containing the interface to which a new 
#     IPv4 address should be assigned
#   * iface -- the interface to witch a new, automatilacy generated, IPv4  
#     address will be assigned
#****

proc autoIPv4addr { node iface } {
    set peer_ip4addrs {}
    set netmaskbits 24 ;# default

	#quasi tempAS
	global tempAS

    if { [[typemodel $node].layer] != "NETWORK" } {
	#
	# Shouldn't get called at all for link-layer nodes
	#
	puts "autoIPv4 called for a [[typemodel $node].layer] layer node"
	return
    }

    # setze IP des ifaceses auf dem node ""
    setIfcIPv4addr $node $iface ""

    set peer_node [logicalPeerByIfc $node $iface]
    # find addresses of NETWORK layer peer nodes
    
  
    if { [[typemodel $peer_node].layer] == "LINK" } {
	#puts "FOUND LIIIIIINK NODE"
	#puts "NODE:"
	#puts $node
	#puts "PEER_NODE"
	#puts $peer_node
	foreach l2node [listLANnodes $peer_node {}] {
	    foreach ifc [ifcList $l2node] {
		set peer [logicalPeerByIfc $l2node $ifc]
		set peer_if [ifcByLogicalPeer $peer $l2node]
		set peer_ip4addr [getIfcIPv4addr $peer $peer_if]
		if { $peer_ip4addr != "" } {
		    lappend peer_ip4addrs [lindex [split $peer_ip4addr /] 0]
		    set netmaskbits [lindex [split $peer_ip4addr /] 1]
		}
	    }
	}


    # point-to-point link with another NETWORK layer peer
    } else {
	#puts "ATTENTION ANOTHER NETWORK LAYER PEER"
	set peer_if [ifcByLogicalPeer $peer_node $node]
	set peer_ip4addr [getIfcIPv4addr $peer_node $peer_if]
	set peer_ip4addrs [lindex [split $peer_ip4addr /] 0]
	if { $peer_ip4addr != "" } {
	    set netmaskbits [lindex [split $peer_ip4addr /] 1]
	}
    }

    # first node connected to wlan should use wlan prefix
    if { [nodeType $peer_node] == "wlan" && 
    	 [llength $peer_ip4addrs] == 0 } {
	# use the special "wireless" pseudo-interface
	set peer_ip4addr [getIfcIPv4addr $peer_node wireless]
	set peer_ip4addrs [lindex [split $peer_ip4addr /] 0]
	set netmaskbits [lindex [split $peer_ip4addr /] 1]
    }
    set nodetype [nodeType $node]
    if { $nodetype == "router" } { set nodetype [getNodeModel $node] }
    switch -exact -- $nodetype {
	router {
	    set targetbyte 1
	}
	host {
	    set targetbyte 10
	}
	PC -
	pc {
	    set targetbyte 20
	}
	default {
	    set targetbyte 1
	}
    }


    # peer has an IPv4 address, allocate a new address on the same network
    if { $peer_ip4addrs != "" } {
	# behandelt diejenige seite der links an die man hinverbindet
	#   und fall wenn router an schon bestehendes switchnetz
	#   angeschlossen wird
	#puts "hinverbunden zu"
	#puts $node

	if { [[typemodel $peer_node].layer] == "LINK" } {
		# hier sind addressen in $peer_ip4addrs
		set ipnet [findFreeIPv4NetLink $node 24 $peer_ip4addrs]
		setIfcIPv4addr $node $iface "$ipnet/24"
	} else {
                set ipnet [findFreeIPv4Net $node 24]
                setIfcIPv4addr $node $iface "$ipnet/30"
}

	set tempAS 999
    } else {
	# behandelt offenbar nur die links von denen man ausgeht
	#puts "ausgegangen von"
	#puts $node

	if { [[typemodel $peer_node].layer] == "LINK" } {
		# hier sind keine addressen in $peer_ip4addrs
		set ipnet [findFreeIPv4NetLink $node 24 $peer_ip4addrs]
		setIfcIPv4addr $node $iface "$ipnet/24"
	} else {
                set ipnet [findFreeIPv4Net $node 24]
                setIfcIPv4addr $node $iface "$ipnet/30"
		#setNodeNetId $peer_node [getASiD $node]
	}
	set tempAS [getASiD $node]
#	puts "tempAS ausgehend"
#	puts $tempAS 
    }
}


#****f* ipv4.tcl/autoIPv4defaultroute 
# NAME
#   autoIPvdefaultroute -- automaticaly assign a default route 
# SYNOPSIS
#   autoIPv4defaultroute $node $iface 
# FUNCTION
#   searches the interface of the node for a router, if a router is found
#   then it is a new default gateway. 
# INPUTS
#   * node  -- default gateway is provided for this node 
#   * iface -- the interface on witch we search for a new default gateway
#****
# schauen ob mit autoIPv4addr interferiert
# -> wenn dann nur wenn nicht LINK und nicht NETWORK
# -> betrifft uns nicht
proc autoIPv4defaultroute { node iface } {
    if { [[typemodel $node].layer] != "NETWORK" } {
	#
	# Shouldn't get called at all for link-layer nodes
	#
	puts "autoIPv4defaultroute called for [[typemodel $node].layer] node"
	return
    }

    set peer_node [logicalPeerByIfc $node $iface]

    if { [[typemodel $peer_node].layer] == "LINK" } {
	foreach l2node [listLANnodes $peer_node {}] {
	    foreach ifc [ifcList $l2node] {
		set peer [logicalPeerByIfc $l2node $ifc]
		if { [nodeType $peer] != "router" && 
		     [nodeType $peer] != "ine" } {
		    continue
		}
		set peer_if [ifcByLogicalPeer $peer $l2node]
		set peer_ip4addr [getIfcIPv4addr $peer $peer_if]
		if { $peer_ip4addr != "" } {
		    set gw [lindex [split $peer_ip4addr /] 0]
		    setStatIPv4routes $node [list "0.0.0.0/0 $gw"]
		    return
		}
	    }
	}
    } else {
	if { [nodeType $peer_node] != "router" && 
	     [nodeType $peer_node] != "ine" } {
	    return
	}
	set peer_if [ifcByLogicalPeer $peer_node $node]
	set peer_ip4addr [getIfcIPv4addr $peer_node $peer_if]
	if { $peer_ip4addr != "" } {
	    set gw [lindex [split $peer_ip4addr /] 0]
	    setStatIPv4routes $node [list "0.0.0.0/0 $gw"]
	    return
	}
    }
}


#****f* ipv4.tcl/checkIPv4Addr 
# NAME
#   checkIPv4Addr -- check the IPv4 address 
# SYNOPSIS
#   set valid [checkIPv4Addr $str]
# FUNCTION
#   Checks if the provided string is a valid IPv4 address. 
# INPUTS
#   * str -- string to be evaluated. Valid IPv4 address is writen in form
#     a.b.c.d 
# RESULT
#   * valid -- function returns 0 if the input string is not in the form
#     of a valid IP address, 1 otherwise
#****

proc checkIPv4Addr { str } {
    set n 0
    if { $str == "" } {
	return 1
    }
    while { $n < 4 } {
	if { $n < 3 } {
	    set i [string first . $str]
	} else {
	    set i [string length $str]
	}
	if { $i < 1 } {
	    return 0
	}
	set part [string range $str 0 [expr $i - 1]]
	if { [string length [string trim $part]] != $i } {
	    return 0
	}
	if { ![string is integer $part] } {
	    return 0
	}
	if { $part < 0 || $part > 255 } {
	    return 0
	}
	set str [string range $str [expr $i + 1] end]
	incr n
    }
    return 1
}


#****f* ipv4.tcl/checkIPv4Net 
# NAME
#   checkIPv4Net -- check the IPv4 network 
# SYNOPSIS
#   set valid [checkIPv4Net $str]
# FUNCTION
#   Checks if the provided string is a valid IPv4 network. 
# INPUTS
#   * str -- string to be evaluated. Valid string is in form a.b.c.d/m 
# RESULT
#   * valid -- function returns 0 if the input string is not in the form
#     of a valid IP address, 1 otherwise
#****

proc checkIPv4Net { str } {
    if { $str == "" } {
	return 1
    }
    if { ![checkIPv4Addr [lindex [split $str /] 0]]} {
	return 0
    }
    set net [string trim [lindex [split $str /] 1]]
    if { [string length $net] == 0 } {
	return 0
    }
    return [checkIntRange $net 0 32]
}

#
# Boeing
# ***** ipv4.tcl/ipv4ToString
# NAME
#  ipv4ToString -- convert 32-bit integer to dotted decimal notation
# ****

proc ipv4ToString { ip } {
	return "[expr ($ip >> 24) & 0xFF].[expr ($ip >> 16) & 0xFF].[expr ($ip >> 8) & 0xFF].[expr $ip & 0xFF]"
}

#
# Boeing
# ***** ipv4.tcl/stringToIPv4
# NAME
#  stringToIPv4 -- convert dotted decimal string to 32-bit integer 
proc stringToIPv4 { ip } {
    set parts [split $ip .]
    set a [lindex $parts 0]; set b [lindex $parts 1];
    set c [lindex $parts 2]; set d [lindex $parts 3];
    return [expr {(($a << 24) + ($b << 16) + ($c << 8) + $d ) & 0xFFFFFFFF}]
}


proc ipv4ToNet { ip prefixlen } {
    set ipn [stringToIPv4 $ip]
    set ones [string repeat 1 $prefixlen]
    set zeroes [string repeat 0 [expr {32 - $prefixlen}]]
    binary scan [binary format B32 $ones$zeroes] H8 mask
    set netn [expr {$ipn & "0x$mask"}]
    return [ipv4ToString $netn]
}

proc getDefaultIPv4Addrs { } {
    return [list "10.0.0.0" "192.168.0.0" "172.16.0.0"]
}

proc isMulticast { str } {
    set i [string first . $str]
    if { $i < 1 } { return false }
    set part [string range $str 0 [expr {$i - 1}]]
    if { ![string is integer $part] } { return false }
    if { $part < 224 || $part > 239 } { return false }
    return true
}

proc ipv4List { node wantmask } {
    set r ""
    foreach ifc [ifcList $node] {
	foreach ip [getIfcIPv4addr $node $ifc] {
	    if { $wantmask } {
		lappend r $ip
	    } else {
		lappend r [lindex [split $ip /] 0]
	    }
	}
    }
    return $r
}


# this can be called with node_list to get a list of all subnets
proc ipv4SubnetList { nodes } {
    set r ""
    foreach node $nodes {
	foreach ipnet [ipv4List $node 1] {
	    set ip [lindex [split $ipnet /] 0]
	    set pl [lindex [split $ipnet /] 1]
	    set net "[ipv4ToNet $ip $pl]/$pl"
	    if { [lsearch $r $net] < 0 } {
		lappend r $net
	    }
	}
    }
    return $r
}
