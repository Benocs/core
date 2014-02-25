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

#****h* imunes/ipv6.tcl
# NAME
#   ipv6.tcl -- file for handeling IPv6
#****

#****f* ipv6.tcl/findFreeIPv6Net
# NAME
#   findFreeIPv6Net -- find free IPv6 network
# SYNOPSIS
#   set ipnet [findFreeIPv4Net $mask]
# FUNCTION
#   Finds a free IPv6 network. Network is concidered to be free
#   if there are no simulated nodes attached to it. 
# INPUTS
#   * mask -- this parameter is left unused for now
# RESULT
#   * ipnet -- returns the free IPv6 network address in the form "a $i". 
#****

proc findFreeIPv6Net { quarknode mask } {
    global g_prefs node_list tempAS

# alle 63er sammeln und  alle 54er sammeln
# -> 7tes und 8tes byte von allen nodes sammeln

  set ipnetsv6 {}

  foreach node $node_list {
    foreach ifc [ifcList $node] {
      # get complete ipv6
      set ipnetv6 [lrange [split [getIfcIPv6addr $node $ifc] ":/"] 0 8]
      if {[lsearch $ipnetsv6 $ipnetv6] == -1} {

        lappend ipnetsv6 $ipnetv6
      }
    }
  }


  set ipnetsv63rds {}

  foreach node $node_list {
    foreach ifc [ifcList $node] {
      # get only 3rd element of every ipv6
      set ipnetv63rd [lrange [split [getIfcIPv6addr $node $ifc] :] 3 3]
      if {[lsearch $ipnetsv63rds $ipnetv63rd] == -1 || [llength [lsearch -all -inline $ipnetsv63rds $ipnetv63rd]] == 1} {

        lappend ipnetsv63rds $ipnetv63rd
      }
    }
  }


  # aufruf von buildInterfaceID
  buildInterfaceID $quarknode

  # asid von quarknode wie bei ipv4
  set i [getASiD $quarknode]
  # von zu ASip abhandeln
  if { [info exists tempAS] } {
    if { $tempAS != 999 } {
      set i $tempAS
    }
  }

  set startv6 0

  for {set j $startv6 } { $j < 65535} { incr j 2 } {

    # pruefen ob >nicht< schon vorhanden
    # TODO da hier nur 3tes element getestet sollte noch
    #    komplette ipv6 auf existenz getestet werden
    set ls_r [lsearch -all -inline $ipnetsv63rds [expr 0x$j]]

    if { [llength $ls_r] == 0 || [llength $ls_r] == 1 } {
      # entweder noch nicht oder erst einmal vorhanden
      set as [string toupper [format %x $i]]

      set subnet [string toupper [format %x $j]]

      set ipnet "FDAA:$as:AAAA:$subnet:[buildInterfaceID $quarknode]"

      return $ipnet
    }

  }

}


# hier werden die letzten 64bit erzeugt
#   parameter: 
#   return: hintere 64bit in der form: >N<ode< >I<nterface
#            NNNN:NNFF:FEII:IIII
proc buildInterfaceID { cur_node } {

  global node_list

  # einfacher zaehler welcher knoten -> davon abgeleitet die mac bestimmen
  set zaehler1 0
  set zaehler2 0
  set nodenr 0
  set ifcnr 0

  foreach node $node_list {

      # soll XX:XX:XX:00:00:00 x ausmachen
      incr zaehler1 
    
      if { $node == $cur_node } {
        foreach ifc [ifcList $node] {
          # soll 00:00:00:XX:XX:XX x ausmachen
          incr zaehler2

        }
        set ifcnr $zaehler2
        set nodenr $zaehler1
        break
      }
  }


  # hier hintere bytes -> steigen bei anzahl der interfaces
  # TODO auch lsb2 betrachte
  set lsb0 0
  set lsb1 0
  set lsb2 0

  for { set z2 0 } { $z2 < $zaehler2 } { incr z2 } {
    set lsb1 $z2
   
    for { set var1 0 } { $var1 < 255 && $z2 < $zaehler2 } { incr var1 } {
      set lsb0 $var1

      # TODO wie war das gemeint. wie bei werten unter 16 fuehrende 0
      incr z2
    }
  }

  if { $lsb0 < 15 } {
    set ipv6_0_0 "0[format %x $lsb0]"
  } else {
    set ipv6_0_0 "[format %x $lsb0]"
  }


  if { $lsb1 < 15 } {
    set ipv6_0_1 "0[format %x $lsb1]"
  } else {
    set ipv6_0_1 "[format %x $lsb1]"
  }

  set ipv6_0 "00:$ipv6_0_1$ipv6_0_0" 


  # hier vordere bytes nach selben muster
  #   wie hintere bytes -> steigen bei anzahl der nodes
  # TODO auch lsb5 behandeln
  set lsb3 0
  set lsb4 0
  set lsb5 0

  for { set z1 0 } { $z1 < $zaehler1 } { incr z1 } {
    set lsb4 $z1
    #puts "$lsb1:$lsb0"
    for { set var2 0 } { $var2 < 255 && $z1 < $zaehler1 } { incr var2 } {
      set lsb3 $var2

      incr z1
    }
  }


  if { $lsb3 < 15 } {
    set ipv6_1_0 "0[format %x $lsb3]"
  } else {
    set ipv6_1_0 "[format %x $lsb3]"
  }



  if { $lsb4 < 15 } {
    set ipv6_1_1 "0[format %x $lsb4]"
  } else {
    set ipv6_1_1 "[format %x $lsb4]"
  }

  set ipv6_1 "00$ipv6_1_1:$ipv6_1_0" 

  set temp "$ipv6_1" 
  append temp "FF:FE$ipv6_0"
  return $temp

}

#****f* ipv6.tcl/findFreeIPv6NetLink
# NAME
#   findFreeIPv6Net -- find free IPv6 network for links to switch
# SYNOPSIS
#   set ipnet [findFreeIPv4NetLink $mask]
# FUNCTION
#   Finds a free IPv6 network. Network is concidered to be free
#   if there are no simulated nodes attached to it. 
# INPUTS
#   * mask -- this parameter is left unused for now
# RESULT
#   * ipnet -- returns the free IPv6 network address in the form "a $i". 
#****
proc findFreeIPv6NetLink { linkNode mask ip6AmSwitchNetzAddressen} {
  global g_prefs node_list tempAS


  set ipnetsv6 {}

  foreach node $node_list {
    foreach ifc [ifcList $node] {
      # get complete ipv6
      set ipnetv6 [lrange [split [getIfcIPv6addr $node $ifc] ":/"] 0 8]
      if {[lsearch $ipnetsv6 $ipnetv6] == -1} {

        lappend ipnetsv6 $ipnetv6
      }
    }
  }


  set ipnetsv63rds {}

  foreach node $node_list {
    foreach ifc [ifcList $node] {
      # get only 3rd element of every ipv6
      set ipnetv63rd [lrange [split [getIfcIPv6addr $node $ifc] :] 3 3]
      if {[lsearch $ipnetsv63rds $ipnetv63rd] == -1 || [llength [lsearch -all -inline $ipnetsv63rds $ipnetv63rd]] == 1} {

        lappend ipnetsv63rds $ipnetv63rd
      }
    }
  }


  # langfristig eine getASiD fuer v4 und eine fuer v6
  #   in richtiger syntax
  set i [getASiD $linkNode]

  if { 0 == [llength $ip6AmSwitchNetzAddressen] } {
    # fall neues 56er
    # solange 56er netz runterzaehlen bis freies entdeckt
    set zahl1 65280

    # von FF00 runter in subnetbits bis freies subnet gefunden
    for { set j $zahl1 } { $j > 0 } { set j [expr $j - 256] } {

      # decimal j in hex -> treffer von ipnetsv63rds in ls_r speichern als HEX
      set ls_r [lsearch -all -inline $ipnetsv63rds [format %x $j]]
      # noch nicht vorhanden -> == 0
      if { [llength $ls_r] == 0 } {
        
        set as [string toupper [format %x $i]]
        

        set subnet [string toupper [format %x $j]]

        # interface komponente von buildInterfaceID ist hier immer 0
        set ipnet "FDAA:$as:AAAA:$subnet:[buildInterfaceID $linkNode]"
        
        return $ipnet

      }
      
    }

  } else {
    # es gibt bereits 56er an peers
    # 56er uebernehmen und hintere 64bit nach schema

    # momentane subnetID der peers -> konkret
    #   des letzten in der liste
    set subnetID [lrange [split [lindex $ip6AmSwitchNetzAddressen end] :] 3 3]

    set as [string toupper [format %x $i]]

    set ipnet "FDAA:$as:AAAA:$subnetID:[buildInterfaceID $linkNode]"

    return $ipnet

  }

}


#****f* ipv6.tcl/autoIPv6addr 
# NAME
#   autoIPv6addr -- automaticaly assign an IPv6 address
# SYNOPSIS
#   autoIPv6addr $node_id $iface 
# FUNCTION
#   automaticaly assignes an IPv6 address to the interface $iface of 
#   of the node $node.
# INPUTS
#   * node_id -- the node containing the interface to witch a new 
#     IPv6 address should be assigned
#   * iface -- the interface to witch a new, automatilacy generated, IPv6  
#     address will be assigned
#****
proc autoIPv6addr { node iface } {
    set peer_ip6addrs {}
    set netmaskbits 63 ;# default

    global tempAS

    setIfcIPv6addr $node $iface ""

    set peer_node [logicalPeerByIfc $node $iface]
    # find addresses of NETWORK layer peer nodes
    if { [[typemodel $peer_node].layer] == "LINK" } {
	foreach l2node [listLANnodes $peer_node {}] {
	    foreach ifc [ifcList $l2node] {
		set peer [logicalPeerByIfc $l2node $ifc]
		set peer_if [ifcByLogicalPeer $peer $l2node]
		set peer_ip6addr [getIfcIPv6addr $peer $peer_if]
		if { $peer_ip6addr != "" } {
		    lappend peer_ip6addrs [lindex [split $peer_ip6addr /] 0]
		    set netmaskbits [lindex [split $peer_ip6addr /] 1]
		}
	    }
	}
    # point-to-point link with another NETWORK layer peer
    } else {
	set peer_if [ifcByLogicalPeer $peer_node $node]
	set peer_ip6addr [getIfcIPv6addr $peer_node $peer_if]
	set peer_ip6addrs [lindex [split $peer_ip6addr /] 0]
	if { $peer_ip6addr != "" } {
	    set netmaskbits [lindex [split $peer_ip6addr /] 1]
	}
    }
    # Boeing: first node connected to wlan should use wlan prefix
    if { [nodeType $peer_node] == "wlan" && 
    	 [llength $peer_ip6addrs] == 0 } {
	# use the special "wireless" pseudo-interface
	set peer_ip6addr [getIfcIPv6addr $peer_node wireless]
	set peer_ip6addrs [lindex [split $peer_ip6addr /] 0]
	set netmaskbits [lindex [split $peer_ip6addr /] 1]
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

    # peer has an IPv6 address, allocate a new address on the same network
    if { $peer_ip6addrs != "" } {
	
        if { [[typemodel $peer_node].layer] == "LINK" } {
                # hier sind addressen in $peer_ip4addrs
                set ipnet [findFreeIPv6NetLink $node 24 $peer_ip6addrs]
                setIfcIPv6addr $node $iface "$ipnet/54"
        } else {
                set ipnet [findFreeIPv6Net $node 24]
                setIfcIPv6addr $node $iface "$ipnet/63"
        }

	set tempAS 999
    } else {

        if { [[typemodel $peer_node].layer] == "LINK" } {
                # hier sind keine addressen in $peer_ip4addrs
                set ipnet [findFreeIPv6NetLink $node 24 $peer_ip6addrs]
                setIfcIPv6addr $node $iface "$ipnet/54"
        } else {
                set ipnet [findFreeIPv6Net $node 24]
                setIfcIPv6addr $node $iface "$ipnet/63"
                #setNodeNetId $peer_node [getASiD $node]
        }

	set tempAS [getASiD $node]
    }
}

#****f* ipv6.tcl/autoIPv6defaultroute 
# NAME
#   autoIPv6defaultroute -- automaticaly assign a default route 
# SYNOPSIS
#   autoIPv6defaultroute $node_id $iface 
# FUNCTION
#   searches the interface of the node for a router, if a router is found
#   then it is a new default gateway. 
# INPUTS
#   * node_id -- default gateway is provided for this node 
#   * iface -- the interface on witch we search for a new default gateway
#****
#TODO schauen ob das mit autoIPv6addr interferiert
proc autoIPv6defaultroute { node iface } {
    if { [[typemodel $node].layer] != "NETWORK" } {
	#
	# Shouldn't get called at all for link-layer nodes
	#
	puts "autoIPv6defaultroute called for [[typemodel $node].layer] node"
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
		set peer_ip6addr [getIfcIPv6addr $peer $peer_if]
		if { $peer_ip6addr != "" } {
		    set gw [lindex [split $peer_ip6addr /] 0]
		    setStatIPv6routes $node [list "::/0 $gw"]
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
	set peer_ip6addr [getIfcIPv6addr $peer_node $peer_if]
	if { $peer_ip6addr != "" } {
	    set gw [lindex [split $peer_ip6addr /] 0]
	    setStatIPv6routes $node [list "::/0 $gw"]
	    return
	}
    }
}

#****f* ipv6.tcl/checkIPv6Addr 
# NAME
#   checkIPv6Addr -- check the IPv6 address 
# SYNOPSIS
#   set valid [checkIPv6Addr $str]
# FUNCTION
#   Checks if the provided string is a valid IPv6 address. 
# INPUTS
#   * str -- string to be evaluated.
# RESULT
#   * valid -- function returns 0 if the input string is not in the form
#     of a valid IP address, 1 otherwise
#****
# TODO schaut nur die syntax an.. nicht etwa ieee vorgaben
proc checkIPv6Addr { str } {
    set doublec false
    set wordlist [split $str :]
    set wordcnt [expr [llength $wordlist] - 1]
    if { $wordcnt < 2 || $wordcnt > 7 } {
	return 0
    }
    if { [lindex $wordlist 0] == "" } {
	set wordlist [lreplace $wordlist 0 0 0]
    }
    if { [lindex $wordlist $wordcnt] == "" } {
	set wordlist [lreplace $wordlist $wordcnt $wordcnt 0]
    }
    for { set i 0 } { $i <= $wordcnt } { incr i } {
	set word [lindex $wordlist $i]
	if { $word == "" } {
	    if { $doublec == "true" } {
		return 0
	    }
	    set doublec true
	}
	if { [string length $word] > 4 } {
	    if { $i == $wordcnt } {
		return [checkIPv4Addr $word]
	    } else {
		return 0
	    }
	}
	if { [string is xdigit $word] == 0 } {
	    return 0
	}
    }
    return 1
}

#****f* ipv6.tcl/checkIPv6Net 
# NAME
#   checkIPv6Net -- check the IPv6 network 
# SYNOPSIS
#   set valid [checkIPv6Net $str]
# FUNCTION
#   Checks if the provided string is a valid IPv6 network. 
# INPUTS
#   * str -- string to be evaluated. Valid string is in form ipv6addr/m 
# RESULT
#   * valid -- function returns 0 if the input string is not in the form
#     of a valid IP address, 1 otherwise.
#****

proc checkIPv6Net { str } {
    if { $str == "" } {
	return 1
    }
    if { ![checkIPv6Addr [lindex [split $str /] 0]]} {
	return 0
    }
    set net [string trim [lindex [split $str /] 1]]
    if { [string length $net] == 0 } {
	return 0
    }
    return [checkIntRange $net 0 128]
}


#
# Boeing
# ***** ipv6.tcl/ipv6ToString
# NAME
#  ipv6ToString -- convert 128-bit number to colon notation
# ****

proc ipv6ToString { ip } {
    set ipv6nums {}
    #binary format c16 H16
    set prevbyte ""
    set prevword ""
    set have_double_colon 0
    foreach byte $ip {
	# group bytes into two-byte hex words
	set hexbyte [format "%x" [expr $byte & 0xFF]]
	if { $prevbyte == "" } {
	    set prevbyte $hexbyte
	} else {
	    if { $prevbyte == 0 } { ;# compress zeroes
		set prevbyte ""
		set hexbyte [format "%x" 0x$hexbyte]
	    } else {
		set hexbyte [format "%02x" 0x$hexbyte]
	    }
	    set twobytes "$prevbyte$hexbyte"
	    set prevbyte ""

	    # compress subsequent zeroes into ::, but only once
	    if { $twobytes == 0 } {
	        if { !$have_double_colon && $prevword == 0} {
		    # replace last 0 with :
		    set ipv6nums [lreplace $ipv6nums end end ""] 
		    set have_double_colon 1
		    set prevword ":"
		    continue ;# don't add current 0 word to list
		} elseif { $prevword == ":" } {
		    continue ;# another zero word, skip it
		}
	    }
	    set prevword $twobytes
    	    lappend ipv6nums $twobytes
	}
    }
    return [join $ipv6nums :]
}

#
# Boeing
# ***** ipv6.tcl/stringToIPv6
# NAME
#  stringToIPv6 -- convert colon notation to 128-bits of binary data
# ****

proc stringToIPv6 { ip } {
    set ip [expandIPv6 $ip]; # remove any double-colon notation
    set parts [split $ip :]

    if { [llength $parts] != 8 } { return "" }; # sanity check
    set bin ""

    foreach part $parts {
	scan $part "%x" num; # convert hex to number
	set binpart [binary format i $num]
	set bin ${bin}${binpart}
    }

    return $bin
}

# expand from double-colon shorthand notation to include all zeros
proc expandIPv6 { ip } {
    set parts [split $ip :]
    set partnum 0
    set expand {}
    set num_zeros 0
    while { [llength $parts] > 0 } {
	set part [lindex $parts 0]; 	# pop off first element
	set parts [lreplace $parts 0 0]

	if {$part == ""} { ; # this is the :: part of the address
	    set num_parts_remain [llength $parts]
	    if { $num_zeros > 0 } { ; # another empty element, another zero
		lappend expand 0
		continue
	    }
	    set num_zeros [expr { 8 - ($partnum + $num_parts_remain) }]
	    for { set i 0 } { $i < $num_zeros } { incr i } {
		lappend expand 0
	    }
	    continue;
	}
	lappend expand $part
	incr partnum
    }
    return [join $expand :]
}

#
# Boeing
# ***** ipv6.tcl/ipv6ToNet
# NAME
#  ipv6ToNet -- convert IPv6 address a:b:c:d:e:f:g:h to a:b:c:d 
# ****

proc ipv6ToNet { ip mask } {
	set ipv6nums [split $ip :] 
	# last remove last to nums of :: num
	set ipv6parts [lrange $ipv6nums 0 [expr [llength $ipv6nums] - 3]]
    	return [join $ipv6parts :]
}




# 
# Boeing
# ***** ipv6.tcl/autoIPv6wlanaddr
# NAME
#  autoIPv6wlanaddr -- part of autoIPv6addr to determine
#  address for node connected to the wlan
# ****
proc autoIPv6wlanaddr { node } {

	# search wlan node for peers, collect IP address into list
	set peer_ip6addrs ""
        foreach ifc [ifcList $node] {
		set peer [logicalPeerByIfc $node $ifc]
		set peer_if [ifcByLogicalPeer $peer $node]
		set peer_ip6addr [getIfcIPv6addr $peer $peer_if]
		if { $peer_ip6addr != "" } {
		    lappend peer_ip6addrs [lindex [split $peer_ip6addr /] 0]
		}
	}
	if { $peer_ip6addrs != "" } {
            set ipnums [split [lindex $peer_ip6addrs 0] :]
            set net "[lindex $ipnums 0]:[lindex $ipnums 1]"
	    set targetbyte 1
            set ipaddr $net\::$targetbyte
            while { [lsearch $peer_ip6addrs $ipaddr] >= 0 } {
                incr targetbyte
                set ipaddr $net\::$targetbyte
            }
	} else {
	    set ipnums [split [getIfcIPv6addr $node wireless] :]
            set net "[lindex $ipnums 0]:[lindex $ipnums 1]"
	    set ipaddr $net\::1
	}
        return "$ipaddr/64"
}

proc getDefaultIPv6Addrs { } {
    global g_prefs
    return [list "FC00::" "FD00::" "2001::" "2002::" "a::"]
}

proc ipv6List { node wantmask } {
    set r ""
    foreach ifc [ifcList $node] {
	foreach ip [getIfcIPv6addr $node $ifc] {
	    if { $wantmask } {
		lappend r $ip
	    } else {
		lappend r [lindex [split $ip /] 0]
	    }
	}
    }
    return $r
}

