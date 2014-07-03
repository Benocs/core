#
# CORE
# Copyright (c)2010-2013 the Boeing Company.
# See the LICENSE file included in this distribution.
#
# authors: Tom Goff <thomas.goff@boeing.com>
#          Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

'''
coreapi.py: uses coreapi_data for Message and TLV types, and defines TLV data
types and objects used for parsing and building CORE API messages.

Overview
****

API-Version: 1.22a

This document defines the communication interface for the Common Open
Research Emulator (CORE). CORE uses this API internally to communicate
between its components. Other systems may connect to CORE using this API to
control the emulated network topology. One example of such an external system
is a physical/link-layer simulator. The API aims to operate on a higher level of
nodes and links, abstracting the lower-level details.

The CORE daemon listens on a TCP socket for CORE API messages from other
local or remote systems. The CORE GUI connects locally to this daemon and
uses this API to instantiate topologies. CORE will also act as an "emulation
server" that listens for a TCP connection from another system. Upon connection
establishment, the other system transmits messages to the CORE daemon that
can control the live-running emulation. Port 4038 was chosen at random from the
IANA list of assigned port numbers (current status is unassigned).


The message types defined by this API are summarized in the following Table: :ref:`table_api_messages-label`

.. _table_api_messages-label:
.. table:: Overview of API Messages

   ======= =============== ===========
   Type    Message Name    Description
   ======= =============== ===========
   1       Node            Adds and removes nodes from an emulation.
   2       Link            Links two nodes together.
   3       Execute         Run a command on a node.
   4       Register        Register an entity with another, for notifications or registering services.
   5       Configuration   Exchange configuration information with CORE.
   6       File            Transfer or copy short files (e.g. configuration files) to a node.
   7       Interface       Add and remove interfaces from nodes.
   8       Event           Signal an event between entities.
   9       Session         Manage emulation sessions.
   10      Exception       Signal errors, warnings, or other exception conditions.
   ======= =============== ===========

**************
Message Format
**************

One or more CORE API control messages may appear in a single TCP data
packet. The CORE API control messages use the following format:

.. _figure_api_message_format:

::

   0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |          Source Port          |       Destination Port        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                        Sequence Number                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Acknowledgment Number                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  Data |           |U|A|P|R|S|F|                               |
   | Offset| Reserved  |R|C|S|S|Y|I|            Window             |
   |       |           |G|K|H|T|N|N|                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |           Checksum            |         Urgent Pointer        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                    Options                    |    Padding    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Message Type  |     Flags     |        Message Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 Message Data (variable length)                |
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Message Type  |     Flags     |        Message Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 Message Data (variable length)                |
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
                                 . . .
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Message Type  |     Flags     |        Message Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 Message Data (variable length)                |
   |                                                               |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+

The TCP header - everything before "Message Type" - represents the standard TCP
header taken from the TCP specification in RFC 793. What follows is one or more
CORE messages. Each Message starts with four bytes that indicate the Message
Type, Flags, and Message Length. A variable Message Data field follows,
depending on the Message Type. Numeric fields are unsigned values expressed in
network byte order where applicable.


The message types defined by this API are summarized in the following Table: :ref:`table_api_message_field-label`

.. _table_api_message_field-label:
.. table:: CORE Message Fields

   ============== ======== ===================================================
   Field          Length   Description
   ============== ======== ===================================================
   Message Type      8 bit Type of CORE message, which defines the contents of

                           the Message Data, required for parsing.
   Flags             8 bit Message flags. Possible values:
                            | 00000001 = 0x01 = Add
                            | 00000010 = 0x02 = Delete
                            | 00000100 = 0x04 = Critical
                            | 00001000 = 0x08 = Local
                            | 00010000 = 0x10 = Status response
                            | 00100000 = 0x20 = Text output
                            | 01000000 = 0x40 = TTY
   Message Length   16 bit Length in bytes of the Message Data. Note that this
                           is represented in network byte order, and excludes
                           the Message Type, Flags, and Message Length fields.
                           he maximum Message Length is 65535 bytes.
   Message Data   variable Data specific to each Message Type, defined in the
                           sections below.
   ============== ======== ===================================================

Each Message Type may implement one or more <Type, Length, Value> tuples, or
TLVs, for representing fields of data. This allows the flexibility of defining
future additional fields. The TCP packet can contain multiple messages, each
which may include several TLVs. This is depicted in Figure
:ref:`API Messages sub-TLVs<figure_api_message_sub_tlvs-label>`.  Each message type defines its own
TLV types. The TLV Length indicates the length in bytes of the TLV data,
excluding the Type and Length fields. For clarity, all of the TLV data fields
shown in Figure :ref:`API Messages sub-TLVs<figure_api_message_sub_tlvs-label>` are 32 bits in length,
but in reality the TLV data can be any length specified by the TLV length field
(up to 255).

The TLV data is padded to align to the 32-bit boundaries, and this padding
length is not included in the TLV length. For 32-bit and 64-bit values,
pre-padding is added (a series of zero bytes) so the actual value is aligned.
Because the Type and Length fields combined occupy 16 bits, there will be
16-bits of padding and then 32-bits of Value for 32-bit values. Strings are
padded at the end to align with the 32-bit boundary.

Although the TLV Length field is limited to 8 bits, imposing a maximum length of
255, special semantics exist for lengthier TLVs. Any TLV exceeding 255 bytes in
length will have a TLV Length field of zero, followed by a 16-bit value (in
network byte order) indicating the TLV length. The variable data field then
follows this 16- bit value. This increases the maximum TLV length to 65,536
bytes; however, the maximum Message Length (for the overall message) is also
limited to 65,536 bytes, so the actual available TLV length depends on the
lengths of all of the TLVs contained in the message.

.. _figure_api_message_sub_tlvs-label:

::

   0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Message Type  |     Flags     |        Message Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  TLV Type     |  TLV Length   |        TLV data (variable)    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  TLV Type     |  TLV Length   |        TLV data (variable)    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |       TLV data (variable, continued, example > 16 bits)       |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Message Type  |     Flags     |        Message Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |  TLV Type     |  TLV Length   |        TLV data (variable)    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+


*************
Message Types
*************

Node Message
============

The Node Message is message type 1. The Node message may cause a variety
of actions to be performed, depending on the message flags:

.. _table_api_node_message_flags:
.. table:: Node Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   No flag (00)            When neither the add or delete flags are set, this
                           message is assumed to modify an existing node or node
                           state.

   Add flag (01)           Message is to create a node or create state for a
                           node.

   Delete flag (10)        Message is to stop a node or delete state for a node.

   Critical flag (100)     Message should be processed, for example if the
                           node's position is unchanged but a link calculation
                           is requested.

   Local flag (1000)       Message is informational, for example to update a
                           display only.

   Status request (10000)  A response message is requested containing the status
                           of this add/delete message.

   (Text output (100000)   This flag is undefined for the Node Message.)
   ======================  ======================================================

The TLVs for the Node Message are defined in Table
:ref:`table_api_node_message_fields` below.

The Node Type TLV determines what type of node will be created. These values are
defined in Table :ref:`table_api_node_type_tlv_values` below. The Model Type
TLV further determines the configuration of the node depending on node types
defined in the GUI (e.g.  router, PC). When the Model Type is not present, its
value defaults to zero.


.. _table_api_node_message_fields:
.. table:: Node Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node Number       Unique number used to identify a
                                               node. Usually node numbering
                                               starts with zero and increments.

   0x02     32 bit           Node Type         Indicates the type of node to be
                                               emulated. See Table
                                               :ref:`table_api_node_type_tlv_values`
                                               for possible values.

   0x03     variable string  Node Name         Text name assigned to a node. The
                                               string does not need to be NULL
                                               terminated as the exact length is
                                               specified in the TLV length. Note
                                               that the node number identifies a
                                               node, not its name.
                                               Unique number used to identify a
                                               node. Usually node numbering
                                               starts with zero and increments.

   0x07     variable string  Model Type        Optional: indicates the model
                                               used for this node type. Assumed
                                               to be "router" if the TLV is
                                               omitted. Used for associating
                                               services with a node. This field
                                               is like a node sub-type that
                                               allows for user-defined types.

   0x08     variable string  Emulation Server  Optional server name on which
                                               this node should be instantiated.

   0x0A     variable string  Session Number(s) Optional numeric identifier(s)
                                               indicating the Session(s) this
                                               message is intended for. A list
                                               of Session numbers may be used,
                                               separated by a pipe "|" symbol.

   0x20     16 bit           X position        Optional: horizontal position
                                               where the node should be drawn
                                               on the logical network map. If
                                               no position is given, CORE
                                               selects the node's position.
                                               The typical width of the CORE
                                               screen is 1024.

   0x21     16 bit           Y position        Optional: vertical position where
                                               the node should be drawn on the
                                               logical network map. If no
                                               position is given, CORE selects
                                               the node's position. The typical
                                               height of the CORE screen is 768.

   0x22     16 bit           Canvas            Optional: canvas number (0 or
                                               higher) on which node should be
                                               drawn with X, Y coordinates. If
                                               omitted, default value is 0.

   0x23     32 bit           Emulation ID      The ID of the emulated node. This
                                               implies that the emulated node
                                               has been instantiated. For
                                               FreeBSD this is the Netgraph ID
                                               of the wireless interface of the
                                               node.

   0x24     32 bit           Network ID        Number identifying the network
                                               this node belongs to. For
                                               example, the node number of the
                                               attached WLAN node. Or the AS
                                               number of the current AS.

   0x25     variable string  Services          List of startup services
                                               configured for this node, string
                                               names are separated by the pipe
                                               "|" character.

   0x42     variable string  Icon              Optional: path of icon file for
                                               display

   0x50     variable string  Opaque data       User-defined data for passing any
                                               type of information.
   ======== ================ ================= =================================


.. _table_api_node_type_tlv_values:
.. table:: Node Type TLV Values

   =============== ========= ===================================================
   Node Type Value Name      Description
   =============== ========= ===================================================
   0x0             Default   Network Namespace (Linux) or jail (FreeBSD) based
                             emulated node.

   0x1             Physical  A physical testbed machine that can is available to
                             be linkedin to the emulation and controlled by
                             CORE.

   0x2             Xen       A Xen based domU node.

   0x3             Undefined

   0x4             Switch    Layer 2 Ethernet bridge, learns connected hosts and
                             unicasts to appropriate link only.

   0x5             Hub       Layer 2 Ethernet hub, forwards data to all
                             connected links.

   0x6             WLAN      Wireless LAN object forwards data intelligently
                             between connected node pairs based on rules.

   0x7             RJ45      Connects physical Ethernet device to the emulation.

   0x8             Tunnel    Uses Span tool/GRE to build tunnels to other
                             emulations or systems.

   0x9             Ktunnel   Uses ng_ksocket to build tunnels from one kernel to
                             another.

   0xA             EMANE     EMANE network uses pluggable MAC/PHY models.
   =============== ========= ===================================================


Link Message
============

The Link Message is message type 2. A Link specifies a connection between two
nodes, specified by their node numbers. The Link message may cause a variety of
actions to be performed, depending on the message flags:


.. _table_api_link_message_flags:
.. table:: Link Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   No flag (00)            When neither the add or delete flags are set, this
                           message is assumed to modify an existing link or link
                           state.

   Add flag (01)           Message is to create a link or create state for a
                           link.

   Delete flag (10)        Message is to remove a link or delete state for a
                           link.

   Critical flag (100)     Message should be processed, for example due to rate
                           limiting.

   Local flag (1000)       Message is informational, for example to update a
                           display only.

   Status request (10000)  A response message is requested containing the status
                           of this add/delete message.

   (Text output (100000)   This flag is undefined for the Link Message.)
   ======================  ======================================================


The TLVs for the Link Message are defined in Table
:ref:`table_api_link_message_fields` below.

.. _table_api_link_message_fields:
.. table:: Link Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node 1 Number     The number of the first node that
                                               the link connects.

   0x02     32 bit           Node 2 Number     The number of the second node
                                               that the link connects.

   0x03     64 bit           Link Delay        The value of the delay of the
                                               link in microseconds (µs),
                                               in network byte order. The value
                                               may be zero (no delay). The
                                               maximum value is 2000000 µs (2
                                               s).

   0x04     64 bit           Link Bandwidth    The value of the bandwidth of
                                               the link in bits per second
                                               (bps), in network byte order.
                                               Sample values are:
                                                | 100000000 = 100M
                                                | 10000000 = 10M
                                                | 512000 = 512 kbps
                                                | 0 = Unrestricted bandwidth.
                                               Up to gigabit speeds are
                                               supported.

   0x05     variable string  PER               The Packet Error Rate, specified
                                               in percent (%), or Bit Error Rate
                                               (FreeBSD). The value should be
                                               between 0-100% inclusive for PER.

   0x06     variable string  Duplicates        The duplicate packet percent (%),
                                               where the specified percentage of
                                               packets will be randomly
                                               duplicated on this link.  The
                                               value may be zero (no
                                               duplicates).  Maximum value is
                                               50%.

   0x07     32 bit           Link Jitter       The value of the random
                                               delay applied to the link in
                                               microseconds (µs), in network
                                               byte order. The value may be zero
                                               (no jitter). The maximum value is
                                               2000000 µs (2 s).

   0x08     16 bit           MER               The Multicast Error Rate,
                                               specified in percent (%).

   0x09     16 bit           Burst             The Burst rate, specified in
                                               percent (%), which is the
                                               conditional probability that the
                                               next packet will be dropped given
                                               the last packet was dropped.

   0x0A     variable string  Session Number(s) Optional numeric identifier(s)
                                               indicating the Session(s) this
                                               message is intended for.  A list
                                               of Session numbers may be used,
                                               separated by a pipe "|" symbol.

   0x0B     16 bit           Priority          Sets the priority of the Link
                                               Message (not a link priority), so
                                               that higher-priority Link
                                               Messages (greater values) can
                                               override lower-priority ones for
                                               a period of time.

   0x10     16 bit           Multicast Burst   The Burst rate for multicast
                                               packets (%)

   0x20     32 bit           Link Message Type Indicates whether this message is
                                               creating/deleting a link (type=1)
                                               or signaling a wireless link
                                               event (type=0).

   0x23     32 bit           Emulation ID      The ID of the emulated node. For
                                               FreeBSD this is the Netgraph ID
                                               of the wireless interface of the
                                               node.  This TLV can appear
                                               multiple times, first for node 1,
                                               then for node 2.

   0x24     32 bit           Network ID        The number of the network to
                                               which this link belongs. This
                                               allows the same node pairs to be
                                               joined to two networks.

   0x25     32 bit           Key               Value used with Tunnel Node t as
                                               the GRE key.

   0x30     16 bit           Interface 1       The number of the interface on
                             Number            Node 1; for example 0 would cause
                                               an interface "eth0" to be
                                               created, 1 would create "eth1",
                                               etc.

   0x31     32 bit           Node 1 IPv4       The IPv4 address assigned to the
                             Address           interface on Node 1;
                                               auto-assigned if not specified.

   0x32     16 bit           Node 1 IPv4       The number of bits forming the
                             Network Mask      network mask for the IPv4 address
                             Length            on Node 1, for example 24 for a
                                               /24 address.

   0x33     64 bit           Node 1 MAC        The MAC address assigned to the
                             Address           interface on Node 1.

   0x34     128 bit          Node 1 IPv6       The IPv6 address assigned to the
                             Address           interface on Node 1.

   0x35     16 bit           Node 1 IPv6       The number of bits forming the
                             Prefix Length     network mask for the IPv6 address
                                               on Node 1.

   0x36     16 bit           Interface 2       The number of the interface on
                             Number            Node 2.

   0x37     32 bit           Node 2 IPv4       The IPv4 address assigned to the
                             Address           interface on Node 2;
                                               auto-assigned if not specified.

   0x38     16 bit           Node 2 IPv4       The number of bits forming the
                             Network Mask      network mask for the IPv4 address
                             Length            on Node 2.

   0x39     64 bit           Node 2 MAC        The MAC address assigned to the
                             Address           interface on Node 2.

   0x40     128 bit          Node 2 IPv6       The IPv6 address assigned to the
                             Address           interface on Node 2.

   0x41     16 bit           Node 2 IPv6       The number of bits forming the
                             Prefix Length     network mask for the IPv6 address
                                               on Node 2.

   0x50     variable string  Opaque Data       User-defined data for passing any
                                               type of information.
   ======== ================ ================= =================================


Execute Message
===============

The Execute Message is message type 3. This message is used to execute the
specified command on the specified node, and respond with the command output
after the command has completed if requested to do so by the message flags.
Because commands will take an unknown amount of time to execute, the resulting
response may take some time to generate, during which time other API messages
may be sent and received. The message features a 32-bit identifier for matching
the original request with the response. No flags are defined. Either the Command
String or Result String TLV may appear in an Execute Message, but not both.

The following flags are used with the Execute Message:

.. _table_api_execute_message_flags:
.. table:: Execute Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           This flag is undefined for the Execute Message,

   Delete flag (10)        Cancel a pending Execute Request Message having the
                           given Execution Number.

   Critical flag (100)     This Execute Request should be immediately executed,
                           regardless of any existing, pending requests for this
                           node.

   Local flag (1000)       This Execute Request should be executed on the host
                           machine, not from within the specified Node; the
                           command being executed affects the specified Node and
                           should be run in the order it was received with other
                           local Execute Requests regarding this Node.

   Status request (10000)  An Execute Response message is requested containing
                           the complete output text of the executed command.

   Text output (100000)    An Execute Response message is requested containing
                           the complete output text of the executed command.

   Terminal req (1000000)  This message requests the command to be executed in
                           order to spawn an interactive user shell on the
                           specified node.
   ======================  ======================================================

The TLVs for the Execute Message are defined in Table
:ref:`table_api_execute_message_fields` below.  Note that the Result String will
likely exceed the TLV length of 255, depending on the output of the specified
command. In that case, the TLV Length field is set to zero, followed by a 16-bit
value specifying the TLV length. The maximum result length is therefore 65536
bytes minus the length of the other TLVs.

.. _table_api_execute_message_fields:
.. table:: Execute Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node Number       The number of the node on which
                                               the command will be executed or
                                               was executed, or the number of
                                               the node that this command is
                                               concerned with.

   0x02     32 bit           Execution Number  An identifier
                                               generated by the caller for
                                               matching an asynchronous
                                               response.

   0x03     32 bit           Execution Time    (Optional TLV) For Execute
                                               Requests, indicates a desired
                                               time for starting command
                                               execution. For Execute Responses,
                                               indicates the time at which
                                               command execution has completed.
                                               The time value represents the
                                               number of seconds since the Epoch
                                               of 00:00:00 UTC January 1, 1970,
                                               as the Unix time(2) and
                                               gettimeofday(2) system calls. A
                                               zero value indicates that the
                                               command should execute
                                               immediately. Absence of this
                                               optional TLV implies a zero
                                               value.

   0x04     variable string  Command String    The presence of this field
                                               indicates an Execute Request
                                               Message. String containing the
                                               exact command to execute. The
                                               string does not need to be NULL
                                               terminated as the exact length is
                                               specified in the TLV length.

   0x05     variable string  Result String     The presence of this field
                                               indicates an Execute Response
                                               Message. String containing the
                                               output of the command that was
                                               run. Note that the string does
                                               not need to be NULL terminated as
                                               the exact length is specified in
                                               the TLV length.

   0x06     32 bit           Result Status     This field may be included in the
                                               Execute Response Message and
                                               contains the numeric exit status
                                               of the executed process.

   0x0A     variable string  Session Number(s) Optional numeric identifier(s)
                                               indicating the Session(s) this
                                               message is intended for.
   ======== ================ ================= =================================


.. _figure_api_execute_message_format:

Execute Message Format::

   0                   1                   2                   3
    0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | Msg Type=3    |0 0 0 0 0 0 0 0|        Message Length         |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | TLV Type=0x01 | TLV Length=4  |          Pad (zero)           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Node Number                           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | TLV Type=0x02 | TLV Length=4  |          Pad (zero)           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Execution Number                      |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | TLV Type=0x03 | TLV Length=4  |          Pad (zero)           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                         Execution Time                        |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   | TLV Type=0x04 | TLV Length=10 |      Command String           |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 ( .. Command String cont.)                    |
   +-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+-+
   |                 ( .. Command String cont.)                    |


Register Message
================

The Register Message is message type 4. This message is used by entities to
register to receive certain notifications from CORE or to register services.

The following flags are used with the Register message:

.. _table_api_register_message_flags:
.. table:: Register Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           Add a registration (same as no flags).
   Delete flag (10)        Remove a registration, i.e. unregister.
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  Request a list of child registrations.
   Text output (100000)    Response of child registrations.
   ======================  ======================================================

Child registrations are defined as follows: if entity 1 registers with entity 2
and requests a list of child registrations, entity 2 will respond with a list of
entities that it currently has registered with itself.

Register TLVs may occur multiple times within a Register message, for example if
there are several Wireless Modules.

The TLVs for the Register Message are defined in Table
:ref:`table_api_register_message_fields` below.

.. _table_api_register_message_fields:
.. table:: Register Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     variable string  Wireless Module   Registers a wireless module for
                                               use with CORE. The string
                                               contains a single modelname. For
                                               example, the string "simple" for
                                               the simple module.

   0x02     variable string  Mobility Module   Registers a mobility module for
                                               use with CORE. The string
                                               contains a single model name. For
                                               example, the string "random
                                               waypoint" for the random waypoint
                                               module.

   0x03     variable string  Utility Module    Registers a utility module for
                                               use with CORE. The string
                                               contains a single model name. For
                                               example, the string "GPS" for the
                                               GPS module.

   0x04     variable string  Execution Server  Registers a daemon that will
                                               handle Execution Messages.

   0x05     variable string  GUI               Registers a GUI that will display
                                               nodes and links. May trigger a
                                               Register Message response back to
                                               the GUI with daemon capabilities.

   0x06     variable string  Emulation Server  Registers a daemon that will
                                               handle emulation of Nodes and
                                               Links.

   0x07     variable string  Relay             Registers a daemon that relays
                                               CORE messages.

   0x0A     variable string  Session Number(s) Optional numeric identifier(s)
                                               indicating the Session(s) this
                                               message is intended for.  A list
                                               of Session numbers may be used,
                                               separated by a pipe "|" symbol.
   ======== ================ ================= =================================


Configuration Message
=====================

The Configuration Message is message type 5. This message is used by an external
entity to exchange configuration information with CORE.

The following flags are used with the Configuration message:

.. _table_api_configuration_message_flags:
.. table:: Configuration Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           undefined
   Delete flag (10)        undefined
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  undefined
   Text output (100000)    undefined
   ======================  ======================================================

Using this Configuration Message, CORE can cause the external entity to provide
configuration defaults and captions for use in a GUI dialog box (for example
when a user clicks configure), and after the dialog box has been filled in, CORE
sends the entered data back to the entity.

The Configuration Message must contain the Configuration Object TLV. This
identifies the object being configured. For example, this string might be one of
the WLAN models listed in a previous Register Message.

The Configuration Message must contain the Configuration Type Flags TLV. This
TLV contains one or more flags indicating the content of the message. The valid
flags are:

.. _table_api_configuration_message_flags_tlv:
.. table:: Configuration Message Flags TLV

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   0001 = 0x01             Request - a response to this message is requested
   0010 = 0x02             Update - update the configuration for this node
                           (this may be used to communicate a Netgraph ID)
   0100 = 0x04             Reset - reset the configuration to its default values
   ======================  ======================================================

The Data Types TLV includes one or more 16-bit values that indicate the data
type for each configuration value. The possible data types are described in
Table :ref:`table_api_configuration_message_data_types`.

.. _table_api_configuration_message_data_types:
.. table:: Data Types TLV Values

   =========== =======================  =============
   Type Number Description              Size in bytes
   =========== =======================  =============
   1            8 bit unsigned value    1
   2            16 bit unsigned value   2
   3            32 bit unsigned value   4
   4            64 bit unsigned value   8
   5            8 bit signed value      1
   6            16 bit signed value     2
   7            32 bit signed value     4
   8            64 bit signed value     8
   9            32 bit floating point   4
                value
   10           NULL-terminated string  variable
   11           boolean value           1
   =========== =======================  =============

The Values TLV contains one or more strings, each representing a value. The
strings are separated by a pipe "|" symbol. These values may be default values
or data supplied by the user.

The Captions TLV contains one or more strings, which may be displayed as
captions in a configuration dialog box. The strings are separated by a pipe "|"
symbol.

Generally, the Data Types, Values, and Captions TLVs will refer to the same
number of configuration items. This number may vary depending on the object
being configured. One additional caption may be specified in the Captions TLV
for display at the bottom of a dialog box.

The TLVs for the Configure Message are defined in Table
:ref:`table_api_configure_message_fields` below.

.. _table_api_configure_message_fields:
.. table:: Configure Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node Number       Node number being configured.
                                               This could be the WLAN node
                                               number, for example.

   0x02     variable string  Configuration     Names the object being
                             Object            configured. This could be the
                                               name of the wireless model, for
                                               example.

   0x03     16 bit           Configuration     Bit flags indicating the type of
                             Type Flags        configuration message. Possible
                                               values are:
                                                | 0001 = 1 = Request
                                                | 0010 = 2 = Update
                                                | 0100 = 4 = Reset

   0x04     variable         Data Types        List of data types for the
                                               associated Values; each type is a
                                               16-bit value.

   0x05     variable string  Values            Text list of configuration
                                               values, separated by a pipe "|"
                                               symbol.

   0x06     variable string  Captions          List of captions for dialog box
                                               display, separated by a pipe "|"
                                               symbol.

   0x07     variable string  Bitmap            Pathname of a bitmap for dialog
                                               box display.

   0x08     variable string  Possible Values   Optional text list of possible
                                               configuration values, separated
                                               by a pipe "|" symbol.  Numeric
                                               value ranges may be specified
                                               with a dash, e.g. "30-70";
                                               individual options may be
                                               specified with a comma, e.g.
                                               "1,2,5.5,11"; text labels for
                                               boolean values, e.g. "on,off".

   0x09     variable string  Value Groups      Optional text list of value
                                               groupings, in the format
                                               "title1:1-5|title2:6-9|10-12",
                                               where title is an optional group
                                               title and i-j is a numeric range
                                               of value indices; groups are
                                               separated by commas.

   0x0A     variable string  Session Number(s) Optionally indicate session
                                               number(s) for this configure
                                               message, possibly overriding the
                                               node number. A list of Session
                                               numbers may be used, separated by
                                               a pipe "|" symbol.

   0x23     32 bit           Emulation ID

   0x24     32 bit           Network ID

   0x50     variable string  Opaque Data       User-defined data for passing any
                                               type of information.
   ======== ================ ================= =================================


File Message
============

The File Message is message type 6. This message is used to transfer a file or a
file location. Because files may be large, compression may be used or, if the
two entities have access to the same file system, this message can provide the
path name to a file.

The following flags are used with the File message:

.. _table_api_file_message_flags:
.. table:: File Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           Truncate Existing File
   Delete flag (10)        Delete File
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  undefined
   Text output (100000)    undefined
   ======================  ======================================================

If the Add flag is specified, any existing file will be truncated. If the Delete
flag is specified, the specified file will be deleted and the file data ignored.
If neither the Add nor Delete flags are used, file data may be appended to the
end of a file if it exists.

If the Node Number TLV is present, the File Name TLV indicates the full path and
name of the file to write on the specified node’s filesystem (where applicable).
If the Node Number TLV is absent, then the File Name TLV indicates the
destination file name on the host’s local filesystem, not the (virtual)
filesystem of one of the nodes.

The Source File Name TLV may optionally be used to specify a path accessible by
the receiving entity. In this case, any file data is ignored, and data is copied
from the source file to the destination file name.

Note that the file data will likely exceed the TLV length of 255, in which case,
the TLV Length field is set to zero, followed by a 16-bit value specifying the
TLV length. The maximum file data length is therefore 65,536 bytes minus the
length of the other TLVs. If the file exceeds 65,536 bytes in length, it should
be transferred in chunks using the File Sequence Number TLV.

The TLVs for the File Message are defined in Table
:ref:`table_api_file_message_fields`.

.. _table_api_file_message_fields:
.. table:: File Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node Number        Indicates the node where the
                                                file should be written. If this
                                                TLV is absent, the file will be
                                                written on the host machine.

   0x02     variable string  File name          The full path and name of the
                                                file to be written.

   0x03     variable string  File mode          Optionally specifies the file
                                                mode bits as used by the
                                                chmod(2) system call.

   0x04     16 bit           File number        Optional file number. May be a
                                                sequence number used to specify
                                                chunks of a file that should be
                                                reassembled, or other semantics
                                                defined by an entity.

   0x05     variable string  File type          Optional file type provided so
                                                the receiving entity knows what
                                                to do with the file (e.g.
                                                service name, session hook.)

   0x06     variable string  Source file name   Specifies a path name of a
                                                source file on the filesystem,
                                                so the file data TLV is not
                                                needed.

   0x0A     variable string  Session Number(s)  Optional numeric identifier(s)
                                                indicating the Session(s) this
                                                message is intended for.  A list
                                                of Session numbers may be used,
                                                separated by a pipe "|" symbol.

   0x10     variable binary  Uncompressed file  The binary uncompressed file
            data             data               data.

   0x11     variable binary  Compressed file    The binary file data that has
            data             data.              been compressed with gzip
                                                compression. *Note: This is not
                                                implemented, yet.*
   ======== ================ ================= =================================

Interface Message
=================

The Interface Message is message type 7. This message will add and remove
interfaces from a node. While interface information may be contained in the Link
messages, this separate message was defined for clarity. Virtual interfaces
typically may be created and destroyed, while physical interfaces are generally
either marked up or down.

If the Add flag is specified, an interface is created. If the Delete flag is
specified, the specified interface will be deleted. If neither the Add nor
Delete flags are used, the interface will be modified according to the given
parameters.

The following flags are used with the Interface message:

.. _table_api_interface_message_flags:
.. table:: Interface Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           Create an Interface
   Delete flag (10)        Delete an Interface
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  undefined
   Text output (100000)    undefined
   ======================  ======================================================


The TLVs for the Interface Message are defined in Table
:ref:`table_api_interface_message_fields`.

.. _table_api_interface_message_fields:
.. table:: Interface Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node Number       Indicates the node associated
                                               with the interface.

   0x02     16 bit           Interface Number  Interface number, for associating
                                               with the interface numbers used
                                               in the Link message.

   0x03     variable string  Interface Name    The name of the interface, for
                                               example "eth3". If this name is
                                               not specified, the name may be
                                               derived from the interface
                                               number.

   0x04     32 bit           IPv4 Address      Optional IPv4 address assigned to
                                               this interface. Value in network
                                               byte order.

   0x05     16 bit           IPv4 Mask         Optional IPv4 network mask.
                                               Requires IPv4 address.

   0x06     64 bit           MAC Address       Optional MAC address assigned to
                                               the interface. Usually only
                                               48-bits of the 64-bit value are
                                               used.

   0x07     128 bit          IPv6 Adress       Optional IPv6 address assigned to
                                               the interface.

   0x08     16 bit           IPv6 Mask         Optional IPv6 network mask.
                                               Requires IPv6 address.

   0x09     16 bit           Interface type    Interface type specifier: 0 =
                                               Wired Ethernet interface, 1 =
                                               Wireless interface, other values
                                               TBD.

   0x0A     variable string  Session Number(s) Optional numeric identifier(s)
                                               indicating the Session(s) this
                                               message is intended for.  A list
                                               of Session numbers may be used,
                                               separated by a pipe "|" symbol.

   0x0B     16 bit           Interface state   0 = Interface is up, 1 =
                                               Interface is down, other values
                                               TBD.

   0x23     32 bit           Emulation ID      The ID of the emulated interface.
                                               On FreeBSD for example this may
                                               be the Netgraph ID.

   0x24     32 bit           Network ID        Number identifying the network
                                               this interface belongs to, for
                                               associating with

   0x30     64 bit           Timestamp         *Optional:* Timestamp in
                                               Microseconds since Epoch when
                                               below counters were captured.

   0x31     64 bit           Bytes In          *Optional:* Bytes In Counter of
                                               the Interface at Timestamp.

   0x32     64 bit           Packets In        *Optional:* Packets In Counter
                                               of the Interface at Timestamp.

   0x33     64 bit           Errors In         *Optional:* Errors In Counter
                                               of the Interface at Timestamp.

   0x34     64 bit           Drop In           *Optional:* Drop In Counter of
                                               the Interface at Timestamp.

   0x35     64 bit           Multicast In      *Optional:* Multicast In Counter
                                               of the Interface at Timestamp.

   0x36     64 bit           Bytes Out         *Optional:* Bytes Out Counter of
                                               the Interface at Timestamp.

   0x37     64 bit           Packets Out       *Optional:* Packets Out Counter
                                               of the Interface at Timestamp.

   0x38     64 bit           Errors Out        *Optional:* Errors Out Counter
                                               of the Interface at Timestamp.

   0x39     64 bit           Drop Out          *Optional:* Drops Out Counter of
                                               the Interface at Timestamp.

   0x3A     64 bit           Multicast Out     *Optional:* Multicast Out Counter
                                               of the Interface at Timestamp.
   ======== ================ ================= =================================


Event Message
=============

The Event Message is message type 8. This message signals an event between
entities or schedules events in a session event queue. For example, here is an
exchange of Event messages when the user presses the "Start" button from the
CORE GUI:

 | GUI Event(type='configuration state') -> CORE Services
 | GUI Node(...) -> Link(...) -> CORE Services
 |      "I am sending you node/link configurations."
 | GUI Event(type='instantiation state') -> CORE Services
 |      "I am done sending node/link configurations. Go ahead with
 |       instantiating the emulation."
 | GUI <- Event(type='runtime state') CORE Services
 |      "The emulation has been started, and entered the runtime state."

Message Flags are currently used only to add and remove scheduled events.
Event Message TLVs are shown in Table :ref:`table_api_interface_message_fields`.
Possible values for the Event Type TLV are listed in Table
:ref:`table_api_event_tlv_values`.

.. _table_api_event_message_flags:
.. table:: Event Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           Add a scheduled event
   Delete flag (10)        Delete a scheduled event
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  undefined
   Text output (100000)    undefined
   ======================  ======================================================

.. _table_api_event_message_fields:
.. table:: Event Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Node Number       Optional. Indicates the node
                                               associated with the Event. When
                                               not specified, the Event may
                                               pertain to all nodes.

   0x02     32 bit           Event Type        Indicates the type of event this
                                               message describes.

   0x03     variable string  Event Name        Optional name associated with the
                                               Event.

   0x04     variable string  Event Data        Optional data associated with the
                                               Event.

   0x05     variable string  Event Time        Event start time in seconds, a
                                               float value in string format.

   0x06     64 bit           Event Number      Optional Event number.

   0x0A     variable string  Session Number(s) Optional numeric identifier(s)
                                               indicating the Session(s) this
                                               message is intended for.  A list
                                               of Session numbers may be used,
                                               separated by a pipe "|" symbol.
   ======== ================ ================= =================================

.. _table_api_event_tlv_values:
.. table:: Event Type TLV Values

   ========== ==================================================================
   TLV Number Description
   ========== ==================================================================
   1          Definition state
   2          Configuration state
   3          Instantiation state
   4          Runtime state
   5          Data collection state
   6          Shutdown state
   7          Start
   8          Stop
   9          Pause
   10         Restart
   11         File Open
   12         File Save
   13         Scheduled
   ========== ==================================================================

Session Message
===============

The Session Message is message type 9. This message is used to exchange
session information between entities.

session information between entities.
The following flags are used with the Session message:

.. _table_api_ession_message_flags:
.. table:: Session Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           Add new session or connect to existing session, if it
                           exists.
   Delete flag (10)        Remove a session and shut it down.
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  Request a list of sessions. If used in conjunction
                           with the Add flag, request a list of session objects
                           upon connecting.
   Text output (100000)    undefined
   ======================  ======================================================

Session Message TLVs are shown in Table :ref:`table_api_session_message_fields`
below. The Session number is required. However, the current session number may
be unknown, and a value of zero can be used to indicate the current session.

.. _table_api_session_message_fields:
.. table:: Session Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     variable string  Session number(s) Unique numeric identifier(s) for
                                               a Session.  A list of Session
                                               numbers may be used, separated by
                                               a pipe "|" symbol.

   0x02     variable string  Session name(s)   Optional name(s) associated with
                                               this Session. A list of Session
                                               names may be used, separated by a
                                               pipe "|" symbol.

   0x03     variable string  Session file(s)   Optional filename(s) associated
                                               with this Session. A list of
                                               Session filenames may be used,
                                               separated by a pipe "|" symbol.

   00x4     variable string  Node count        Optional number of nodes in this
                                               session. A list of number of
                                               nodes may be used, separated by a
                                               pipe "|" symbol.

   0x05     variable string  Date              Date and time the session was
                                               started.

   0x06     variable string  Thumbnail File    Optional thumbnail filename for
                                               displaying a preview image of
                                               this session.

   0x07     variable string  Username          Option username. Used to inform
                                               which user is connecting to a
                                               session, for helping with, e.g.
                                               file permissions.

   0x0a     variable string  Session opaque    Opaque data associated with this
                                               Session.
   ======== ================ ================= =================================

Exception Message
=================

The Exception Message is message type 10 (0x0A). This message is used to
notify components of warnings, errors, or other exceptions.

No flags are defined for the Exception Message.

.. _table_api_exception_message_flags:
.. table:: Exception Message Flags

   ======================  ======================================================
   Flag                    Description
   ======================  ======================================================
   Add flag (01)           undefined
   Delete flag (10)        undefined
   Critical flag (100)     undefined
   Local flag (1000)       undefined
   Status request (10000)  undefined
   Text output (100000)    undefined
   ======================  ======================================================


Exception Message TLVs are shown in Table
:ref:`table_api_exception_message_fields` below. The Exception Level is
required.

.. _table_api_exception_message_fields:
.. table:: Exception Message Fields

   ======== ================ ================= =================================
   TLV type TLV length       Name              Description
   ======== ================ ================= =================================
   0x01     32 bit           Exception Node    Optional node number indicating
                             number            the exception is associated with
                                               a node.

   0x02     variable string  Exception Session Optional numeric identifier(s)
                             number(s)         associating the exception with
                                               one or more Sessions. A list of
                                               Session numbers may be used,
                                               separated by a pipe "|" symbol.

   0x03     16 bit           Level             Required numeric value used to
                                               indicate level of severity for
                                               this exception.

   0x04     variable string  Source            Optional text indicating the name
                                               of the component the generated
                                               the exception.

   0x05     variable string  Date              Date and time string of when the
                                               exception was thrown.

   0x06     variable string  Exception Text    Required text describing the
                                               exception.

   0x0A     variable string  Exception opaque  Opaque data associated with this
                                               Exception.
   ======== ================ ================= =================================

Exception Levels, used to indicate the severity of the exception, are defined in
Table :ref:`table_api_exception_message_levels` below.

.. _table_api_exception_message_levels:
.. table:: Exception Levels

   =============== =============================================================
   Exception Level Description
   =============== =============================================================
   1               Fatal Error
   2               Error
   3               Warning
   4               Notice
   =============== =============================================================


Change Log
==========

.. _table_api_changelog:
.. table:: Change Log

   ================ ======== ===================================================
   Version          Date     Description
   ================ ======== ===================================================
   1.0              02/06/06 initial revision

   1.1              02/15/06 added the TLV format to allow flexibility in
                             defining various fields that are suggested by Dan
                             Mackley.

   1.2              02/16/06 allow multiple nodes per packet as suggested by DM

   1.3              04/04/06 update fields to 32-bits, add padding for 32-bit
                             boundary; total length changed to sequence number

   1.4              07/20/06 add IP, IPv6, and MAC address fields to Node
                             Message

   1.5              09/01/06 correction of type/length field to 8 bits in all
                             sections

   1.6              09/20/06 addition of "Canvas" selection for node location
                             specification

   1.7              02/14/07 renamed to CORE API, removed message header

   1.8              08/01/07 added Execute Message; fix Link Message diagram;
                             other minor fixes

   1.9              12/03/07 added Register Message; increase TLV lengths for
                             link parameters, added some new TLVs, allow TLV
                             length of 65,536, remove some figures

   1.10             12/18/07 changed order of link effect TLVs; BER becomes PER

   1.10             01/03/08 updated formatting

   1.11             01/09/08 added Configuration Message

   1.12             04/15/08 enhanced Register Message with additional module
                             types; added types to Data Types TLV; Data Values
                             TLV into string; distinguish between Emulation ID
                             and Network ID, no longer overloading Node Number
                             with Netgraph IDs; list maximum values and fix
                             packet error rate to %

   1.13             05/15/08 Added separate Node Type table and new Model Type
                             TLV for the Node Message; added critical flag

   1.14             11/12/08 Added Exec Server TLV to Register Message; added
                             link type, interface numbers, and addressing TLVs
                             to Link message; added MER, burst and multicast
                             burst effects to Link message; use 64-bit number
                             for MAC addresses instead of 48-bit; added local,
                             status, and text flags; added Exec Status TLV

   1.15             06/19/09 Added File Message, GUI and server TLVs for
                             Register; updated overview text

   1.16 (CORE 4.0)  08/06/10 Added Interface, Event, and Session Messages.
                             Updated the overview section. Added Relay type to
                             Register message.  Added model type for WLAN nodes.
                             Added EMANE node type and Opaque node TLV.  Changed
                             lat/long/alt Node TLVs to strings.  Added Possible
                             Values and Groups TLVs to Configuration message
                             along with boolean data type. Added Emulation
                             Server TLV to Node Message.

   1.17 (CORE 4.1)  12/23/10 Added services TLV to Node Message, Session Number
                             and Opaque Data to Configuration and Link Messages.
                             Added Key TLV to Link Message. Node Model TLV
                             changed from 32-bit to string. PER changed to
                             64-bit value.

   1.18 (CORE 4.2)  08/18/11 Changed node types to accommodate different machine
                             types, removing XORP, PC, Host types, which are now
                             represented by node services.  Changed link type
                             TLV to separate wireless link/unlink events.
                             Removed heading, platform type, platform ID TLVs
                             from node message.  Added flags and user TLV to
                             Session Message.

   1.19 (CORE 4.3)  02/10/12 Added Exception Message. Changed File Type TLV to
                             string in File Message. Added File Open and File
                             Save event types.

   1.20 (CORE 4.4)  07/30/12 Added Session TLV to all messages (except Session,
                             Exception) for connectionless messages, and changed
                             Configuration Message Session TLV to a string.
                             Added link TLVs for color and width. Added support
                             for scheduled events, event time, and event number
                             to the Event Message.

   1.21 (CORE 4.5)  03/20/13 Removed unused TLVs from Conf Message and Node
                             Message; removed deprecated table of model types
                             from Node Message.

   1.22 (CORE 4.6)  09/25/13 Added priority field to Link Message. Changed Link
                             Loss (PER) and Duplicates to string values to
                             support floats.

   1.22a            02/24/14 Added TLVs for interface counters to Interface
                             Message.
   ================ ======== ===================================================

'''

import struct

from core.api.data import *
from core.misc.ipaddr import *


class CoreTlvData(object):
    datafmt = None
    datatype = None
    padlen = None

    @classmethod
    def pack(cls, value):
        "return: (tlvlen, tlvdata)"
        tmp = struct.pack(cls.datafmt, value)
        return len(tmp) - cls.padlen, tmp

    @classmethod
    def unpack(cls, data):
        return struct.unpack(cls.datafmt, data)[0]

    @classmethod
    def packstring(cls, strvalue):
        return cls.pack(cls.fromstring(strvalue))

    @classmethod
    def fromstring(cls, s):
        return cls.datatype(s)

class CoreTlvDataObj(CoreTlvData):
    @classmethod
    def pack(cls, obj):
        "return: (tlvlen, tlvdata)"
        value = cls.getvalue(obj)
        if not isinstance(value, bytes):
          value = bytes(value, encoding = 'utf-8')
        tmp = struct.pack(cls.datafmt, value)
        return len(tmp) - cls.padlen, tmp

    @classmethod
    def unpack(cls, data):
        return cls.newobj(struct.unpack(cls.datafmt, data)[0])

    @staticmethod
    def getvalue(obj):
        raise NotImplementedError

    @staticmethod
    def newobj(obj):
        raise NotImplementedError

class CoreTlvDataUint16(CoreTlvData):
    datafmt = "!H"
    datatype = int
    padlen = 0

class CoreTlvDataUint32(CoreTlvData):
    datafmt = "!2xI"
    datatype = int
    padlen = 2

class CoreTlvDataUint64(CoreTlvData):
    datafmt = "!2xQ"
    datatype = int
    padlen = 2

class CoreTlvDataString(CoreTlvData):
    datatype = str

    @staticmethod
    def pack(value):
        if isinstance(value, bytes):
            value = value.decode()
        elif not isinstance(value, str):
            raise ValueError("value not a string: %s" % value)
        if len(value) < 256:
            hdrsiz = CoreTlv.hdrsiz
        else:
            hdrsiz = CoreTlv.longhdrsiz
        padlen = -(hdrsiz + len(value)) % 4
        return len(value), bytes(value, encoding = 'utf-8') + (b'\0' * padlen)

    @staticmethod
    def unpack(data):
        return data.decode().rstrip('\0')

class CoreTlvDataUint16List(CoreTlvData):
    ''' List of unsigned 16-bit values.
    '''
    datatype = tuple

    @staticmethod
    def pack(values):
        if not isinstance(values, tuple):
            raise ValueError("value not a tuple: %s" % values)
        data = b""
        for v in values:
            data += struct.pack("!H", v)
        padlen = -(CoreTlv.hdrsiz + len(data)) % 4
        return len(data), data + (b'\0' * padlen)

    @staticmethod
    def unpack(data):
        datafmt = "!%dH" % (len(data)/2)
        return struct.unpack(datafmt, data)

    @classmethod
    def fromstring(cls, s):
        return tuple([int(x) for x in s.split()])

class CoreTlvDataIPv4Addr(CoreTlvDataObj):
    datafmt = "!2x4s"
    datatype = IPAddr.fromstring
    padlen = 2

    @staticmethod
    def getvalue(obj):
        return obj.addr.packed

    @staticmethod
    def newobj(value):
        return IPAddr(af = AF_INET, addr = value)

class CoreTlvDataIPv6Addr(CoreTlvDataObj):
    datafmt = "!16s2x"
    datatype = IPAddr.fromstring
    padlen = 2

    @staticmethod
    def getvalue(obj):
        return obj.addr.packed

    @staticmethod
    def newobj(value):
        return IPAddr(af = AF_INET6, addr = value)

class CoreTlvDataMacAddr(CoreTlvDataObj):
    datafmt = "!2x8s"
    datatype = MacAddr.fromstring
    padlen = 2

    @staticmethod
    def getvalue(obj):
        return obj.addr

    @staticmethod
    def newobj(value):
        return MacAddr(addr = value[2:]) # only use 48 bits

class CoreTlv(object):
    hdrfmt = "!BB"
    hdrsiz = struct.calcsize(hdrfmt)

    longhdrfmt = "!BBH"
    longhdrsiz = struct.calcsize(longhdrfmt)

    tlvtypemap = {}
    tlvdataclsmap = {}

    def __init__(self, tlvtype, tlvdata):
        self.tlvtype = tlvtype
        if tlvdata:
            try:
                self.value = self.tlvdataclsmap[self.tlvtype].unpack(tlvdata)
            except KeyError:
                self.value = tlvdata
        else:
            self.value = None

    @classmethod
    def unpack(cls, data):
        "parse data and return (tlv, remainingdata)"
        tlvtype, tlvlen = struct.unpack(cls.hdrfmt, data[:cls.hdrsiz])
        hdrsiz = cls.hdrsiz
        if tlvlen == 0:
            tlvtype, zero, tlvlen = struct.unpack(cls.longhdrfmt,
                                                  data[:cls.longhdrsiz])
            hdrsiz = cls.longhdrsiz
        tlvsiz = hdrsiz + tlvlen
        tlvsiz += -tlvsiz % 4           # for 32-bit alignment
        return cls(tlvtype, data[hdrsiz:tlvsiz]), data[tlvsiz:]

    @classmethod
    def pack(cls, tlvtype, value):
        try:
            tlvlen, tlvdata = cls.tlvdataclsmap[tlvtype].pack(value)
        except Exception as e:
            raise ValueError("TLV packing error type=%s: %s" % (tlvtype, e))
        if tlvlen < 256:
            hdr = struct.pack(cls.hdrfmt, tlvtype, tlvlen)
        else:
            hdr = struct.pack(cls.longhdrfmt, tlvtype, 0, tlvlen)
        return hdr + tlvdata

    @classmethod
    def packstring(cls, tlvtype, value):
        return cls.pack(tlvtype, cls.tlvdataclsmap[tlvtype].fromstring(value))

    def typestr(self):
        try:
            return self.tlvtypemap[self.tlvtype]
        except KeyError:
            return "unknown tlv type: %s" % str(self.tlvtype)

    def __str__(self):
        return "%s (tlvtype = %s, value = %s)" % \
               (self.__class__.__name__, self.typestr(), self.value)

class CoreNodeTlv(CoreTlv):
    tlvtypemap = node_tlvs
    tlvdataclsmap = {
        CORE_TLV_NODE_NUMBER: CoreTlvDataUint32,
        CORE_TLV_NODE_TYPE: CoreTlvDataUint32,
        CORE_TLV_NODE_NAME: CoreTlvDataString,
        CORE_TLV_NODE_IPADDR: CoreTlvDataIPv4Addr,
        CORE_TLV_NODE_MACADDR: CoreTlvDataMacAddr,
        CORE_TLV_NODE_IP6ADDR: CoreTlvDataIPv6Addr,
        CORE_TLV_NODE_MODEL: CoreTlvDataString,
        CORE_TLV_NODE_EMUSRV: CoreTlvDataString,
        CORE_TLV_NODE_SESSION: CoreTlvDataString,
        CORE_TLV_NODE_XPOS: CoreTlvDataUint16,
        CORE_TLV_NODE_YPOS: CoreTlvDataUint16,
        CORE_TLV_NODE_CANVAS: CoreTlvDataUint16,
        CORE_TLV_NODE_EMUID: CoreTlvDataUint32,
        CORE_TLV_NODE_NETID: CoreTlvDataUint32,
        CORE_TLV_NODE_SERVICES: CoreTlvDataString,
        CORE_TLV_NODE_LAT: CoreTlvDataString,
        CORE_TLV_NODE_LONG: CoreTlvDataString,
        CORE_TLV_NODE_ALT: CoreTlvDataString,
        CORE_TLV_NODE_ICON: CoreTlvDataString,
        CORE_TLV_NODE_OPAQUE: CoreTlvDataString,
    }

class CoreLinkTlv(CoreTlv):
    tlvtypemap = link_tlvs
    tlvdataclsmap = {
        CORE_TLV_LINK_N1NUMBER: CoreTlvDataUint32,
        CORE_TLV_LINK_N2NUMBER: CoreTlvDataUint32,
        CORE_TLV_LINK_DELAY: CoreTlvDataUint64,
        CORE_TLV_LINK_BW: CoreTlvDataUint64,
        CORE_TLV_LINK_PER: CoreTlvDataString,
        CORE_TLV_LINK_DUP: CoreTlvDataString,
        CORE_TLV_LINK_JITTER: CoreTlvDataUint64,
        CORE_TLV_LINK_MER: CoreTlvDataUint16,
        CORE_TLV_LINK_BURST: CoreTlvDataUint16,
        CORE_TLV_LINK_SESSION: CoreTlvDataString,
        CORE_TLV_LINK_MBURST: CoreTlvDataUint16,
        CORE_TLV_LINK_TYPE: CoreTlvDataUint32,
        CORE_TLV_LINK_GUIATTR: CoreTlvDataString,
        CORE_TLV_LINK_UNI: CoreTlvDataUint16,
        CORE_TLV_LINK_EMUID: CoreTlvDataUint32,
        CORE_TLV_LINK_NETID: CoreTlvDataUint32,
        CORE_TLV_LINK_KEY: CoreTlvDataUint32,
        CORE_TLV_LINK_IF1NUM: CoreTlvDataUint16,
        CORE_TLV_LINK_IF1IP4: CoreTlvDataIPv4Addr,
        CORE_TLV_LINK_IF1IP4MASK: CoreTlvDataUint16,
        CORE_TLV_LINK_IF1MAC: CoreTlvDataMacAddr,
        CORE_TLV_LINK_IF1IP6: CoreTlvDataIPv6Addr,
        CORE_TLV_LINK_IF1IP6MASK: CoreTlvDataUint16,
        CORE_TLV_LINK_IF2NUM: CoreTlvDataUint16,
        CORE_TLV_LINK_IF2IP4: CoreTlvDataIPv4Addr,
        CORE_TLV_LINK_IF2IP4MASK: CoreTlvDataUint16,
        CORE_TLV_LINK_IF2MAC: CoreTlvDataMacAddr,
        CORE_TLV_LINK_IF2IP6: CoreTlvDataIPv6Addr,
        CORE_TLV_LINK_IF2IP6MASK: CoreTlvDataUint16,
        CORE_TLV_LINK_OPAQUE: CoreTlvDataString,
    }

class CoreExecTlv(CoreTlv):
    tlvtypemap = exec_tlvs
    tlvdataclsmap = {
        CORE_TLV_EXEC_NODE: CoreTlvDataUint32,
        CORE_TLV_EXEC_NUM: CoreTlvDataUint32,
        CORE_TLV_EXEC_TIME: CoreTlvDataUint32,
        CORE_TLV_EXEC_CMD: CoreTlvDataString,
        CORE_TLV_EXEC_RESULT: CoreTlvDataString,
        CORE_TLV_EXEC_STATUS: CoreTlvDataUint32,
        CORE_TLV_EXEC_SESSION: CoreTlvDataString,
    }

class CoreRegTlv(CoreTlv):
    tlvtypemap = reg_tlvs
    tlvdataclsmap = {
        CORE_TLV_REG_WIRELESS: CoreTlvDataString,
        CORE_TLV_REG_MOBILITY: CoreTlvDataString,
        CORE_TLV_REG_UTILITY: CoreTlvDataString,
        CORE_TLV_REG_EXECSRV: CoreTlvDataString,
        CORE_TLV_REG_GUI: CoreTlvDataString,
        CORE_TLV_REG_EMULSRV: CoreTlvDataString,
        CORE_TLV_REG_SESSION: CoreTlvDataString,
    }

class CoreConfTlv(CoreTlv):
    tlvtypemap = conf_tlvs
    tlvdataclsmap = {
        CORE_TLV_CONF_NODE: CoreTlvDataUint32,
        CORE_TLV_CONF_OBJ: CoreTlvDataString,
        CORE_TLV_CONF_TYPE: CoreTlvDataUint16,
        CORE_TLV_CONF_DATA_TYPES: CoreTlvDataUint16List,
        CORE_TLV_CONF_VALUES: CoreTlvDataString,
        CORE_TLV_CONF_CAPTIONS: CoreTlvDataString,
        CORE_TLV_CONF_BITMAP: CoreTlvDataString,
        CORE_TLV_CONF_POSSIBLE_VALUES: CoreTlvDataString,
        CORE_TLV_CONF_GROUPS: CoreTlvDataString,
        CORE_TLV_CONF_SESSION: CoreTlvDataString,
        CORE_TLV_CONF_NETID: CoreTlvDataUint32,
        CORE_TLV_CONF_OPAQUE: CoreTlvDataString,
    }

class CoreFileTlv(CoreTlv):
    tlvtypemap = file_tlvs
    tlvdataclsmap = {
        CORE_TLV_FILE_NODE: CoreTlvDataUint32,
        CORE_TLV_FILE_NAME: CoreTlvDataString,
        CORE_TLV_FILE_MODE: CoreTlvDataString,
        CORE_TLV_FILE_NUM: CoreTlvDataUint16,
        CORE_TLV_FILE_TYPE: CoreTlvDataString,
        CORE_TLV_FILE_SRCNAME: CoreTlvDataString,
        CORE_TLV_FILE_SESSION: CoreTlvDataString,
        CORE_TLV_FILE_DATA: CoreTlvDataString,
        CORE_TLV_FILE_CMPDATA: CoreTlvDataString,
    }

class CoreIfaceTlv(CoreTlv):
    tlvtypemap = iface_tlvs
    tlvdataclsmap = {
        CORE_TLV_IFACE_NODE: CoreTlvDataUint32,
        CORE_TLV_IFACE_NUM: CoreTlvDataUint16,
        CORE_TLV_IFACE_NAME: CoreTlvDataString,
        CORE_TLV_IFACE_IPADDR: CoreTlvDataIPv4Addr,
        CORE_TLV_IFACE_MASK: CoreTlvDataUint16,
        CORE_TLV_IFACE_MACADDR: CoreTlvDataMacAddr,
        CORE_TLV_IFACE_IP6ADDR: CoreTlvDataIPv6Addr,
        CORE_TLV_IFACE_IP6MASK: CoreTlvDataUint16,
        CORE_TLV_IFACE_TYPE: CoreTlvDataUint16,
        CORE_TLV_IFACE_SESSION: CoreTlvDataString,
        CORE_TLV_IFACE_STATE: CoreTlvDataUint16,
        CORE_TLV_IFACE_EMUID: CoreTlvDataUint32,
        CORE_TLV_IFACE_NETID: CoreTlvDataUint32,
        CORE_TLV_IFACE_TIMESTAMP: CoreTlvDataUint64,
        CORE_TLV_IFACE_BYTESIN: CoreTlvDataUint64,
        CORE_TLV_IFACE_PACKETSIN: CoreTlvDataUint64,
        CORE_TLV_IFACE_ERRORSIN: CoreTlvDataUint64,
        CORE_TLV_IFACE_DROPIN: CoreTlvDataUint64,
        CORE_TLV_IFACE_MCASTIN: CoreTlvDataUint64,
        CORE_TLV_IFACE_BYTESOUT: CoreTlvDataUint64,
        CORE_TLV_IFACE_PACKETSOUT: CoreTlvDataUint64,
        CORE_TLV_IFACE_ERRORSOUT: CoreTlvDataUint64,
        CORE_TLV_IFACE_DROPOUT: CoreTlvDataUint64,
        CORE_TLV_IFACE_MCASTOUT: CoreTlvDataUint64,
    }

class CoreEventTlv(CoreTlv):
    tlvtypemap = event_tlvs
    tlvdataclsmap = {
        CORE_TLV_EVENT_NODE: CoreTlvDataUint32,
        CORE_TLV_EVENT_TYPE: CoreTlvDataUint32,
        CORE_TLV_EVENT_NAME: CoreTlvDataString,
        CORE_TLV_EVENT_DATA: CoreTlvDataString,
        CORE_TLV_EVENT_TIME: CoreTlvDataString,
        CORE_TLV_EVENT_SESSION: CoreTlvDataString,
    }

class CoreSessionTlv(CoreTlv):
    tlvtypemap = session_tlvs
    tlvdataclsmap = {
        CORE_TLV_SESS_NUMBER: CoreTlvDataString,
        CORE_TLV_SESS_NAME: CoreTlvDataString,
        CORE_TLV_SESS_FILE: CoreTlvDataString,
        CORE_TLV_SESS_NODECOUNT: CoreTlvDataString,
        CORE_TLV_SESS_DATE: CoreTlvDataString,
        CORE_TLV_SESS_THUMB: CoreTlvDataString,
        CORE_TLV_SESS_USER: CoreTlvDataString,
        CORE_TLV_SESS_OPAQUE: CoreTlvDataString,
    }

class CoreExceptionTlv(CoreTlv):
    tlvtypemap = exception_tlvs
    tlvdataclsmap = {
        CORE_TLV_EXCP_NODE: CoreTlvDataUint32,
        CORE_TLV_EXCP_SESSION: CoreTlvDataString,
        CORE_TLV_EXCP_LEVEL: CoreTlvDataUint16,
        CORE_TLV_EXCP_SOURCE: CoreTlvDataString,
        CORE_TLV_EXCP_DATE: CoreTlvDataString,
        CORE_TLV_EXCP_TEXT: CoreTlvDataString,
        CORE_TLV_EXCP_OPAQUE: CoreTlvDataString,
    }


class CoreMessage(object):
    hdrfmt = "!BBH"
    hdrsiz = struct.calcsize(hdrfmt)

    msgtype = None

    flagmap = {}

    tlvcls = CoreTlv

    def __init__(self, flags, hdr, data):
        if not isinstance(hdr, bytes):
          hdr = bytes(hdr, encoding = 'utf-8')
        if not isinstance(data, bytes):
          data = bytes(data, encoding = 'utf-8')
        self.rawmsg = hdr + data
        self.flags = flags
        self.tlvdata = {}
        self.parsedata(data)

    @classmethod
    def unpackhdr(cls, data):
        "parse data and return (msgtype, msgflags, msglen)"
        msgtype, msgflags, msglen = struct.unpack(cls.hdrfmt, data[:cls.hdrsiz])
        return msgtype, msgflags, msglen

    @classmethod
    def pack(cls, msgflags, tlvdata):
        hdr = struct.pack(cls.hdrfmt, cls.msgtype, msgflags, len(tlvdata))
        return hdr + tlvdata

    def addtlvdata(self, k, v):
        if k in self.tlvdata:
            raise KeyError("key already exists: %s (val=%s)" % (k, v))
        self.tlvdata[k] = v

    def gettlv(self, tlvtype):
        if tlvtype in self.tlvdata:
            return self.tlvdata[tlvtype]
        else:
            return None

    def parsedata(self, data):
        while data:
            tlv, data = self.tlvcls.unpack(data)
            self.addtlvdata(tlv.tlvtype, tlv.value)

    def packtlvdata(self):
        ''' Opposite of parsedata(). Return packed TLV data using
        self.tlvdata dict. Used by repack().
        '''
        tlvdata = b""
        keys = sorted(self.tlvdata.keys())
        for k in keys:
            v = self.tlvdata[k]
            tlvdata += self.tlvcls.pack(k, v)
        return tlvdata

    def repack(self):
        ''' Invoke after updating self.tlvdata[] to rebuild self.rawmsg.
        Useful for modifying a message that has been parsed, before
        sending the raw data again.
        '''
        tlvdata = self.packtlvdata()
        self.rawmsg = self.pack(self.flags, tlvdata)

    def typestr(self):
        try:
            return message_types[self.msgtype]
        except KeyError:
            return "unknown message type: %s" % str(self.msgtype)

    def flagstr(self):
        msgflags = []
        flag = 1
        while True:
            if (self.flags & flag):
                try:
                    msgflags.append(self.flagmap[flag])
                except KeyError:
                    msgflags.append("0x%x" % flag)
            flag <<= 1
            if not (self.flags & ~(flag - 1)):
                break
        return "0x%x (%s)" % (self.flags, " | ".join(msgflags))

    def __str__(self):
        tmp = "%s (msgtype = %s, flags = %s)" % \
              (self.__class__.__name__, self.typestr(), self.flagstr())
        for k, v in list(self.tlvdata.items()):
            if k in self.tlvcls.tlvtypemap:
                tlvtype = self.tlvcls.tlvtypemap[k]
            else:
                tlvtype = "tlv type %s" % k
            tmp += "\n  %s=> %s" % (tlvtype, v)
        return tmp

    def nodenumbers(self):
        ''' Return a list of node numbers included in this message.
        '''
        n = None
        n2 = None
        # not all messages have node numbers
        if self.msgtype == CORE_API_NODE_MSG:
            n = self.gettlv(CORE_TLV_NODE_NUMBER)
        elif self.msgtype == CORE_API_LINK_MSG:
            n = self.gettlv(CORE_TLV_LINK_N1NUMBER)
            n2 = self.gettlv(CORE_TLV_LINK_N2NUMBER)
        elif self.msgtype == CORE_API_EXEC_MSG:
            n = self.gettlv(CORE_TLV_EXEC_NODE)
        elif self.msgtype == CORE_API_CONF_MSG:
            n = self.gettlv(CORE_TLV_CONF_NODE)
        elif self.msgtype == CORE_API_FILE_MSG:
            n = self.gettlv(CORE_TLV_FILE_NODE)
        elif self.msgtype == CORE_API_IFACE_MSG:
            n = self.gettlv(CORE_TLV_IFACE_NODE)
        elif self.msgtype == CORE_API_EVENT_MSG:
            n = self.gettlv(CORE_TLV_EVENT_NODE)
        r = []
        if n is not None:
            r.append(n)
        if n2 is not None:
            r.append(n2)
        return r

    def sessionnumbers(self):
        ''' Return a list of session numbers included in this message.
        '''
        r = []
        if self.msgtype == CORE_API_SESS_MSG:
            s = self.gettlv(CORE_TLV_SESS_NUMBER)
        elif self.msgtype == CORE_API_EXCP_MSG:
            s = self.gettlv(CORE_TLV_EXCP_SESSION)
        else:
            # All other messages share TLV number 0xA for the session number(s).
            s = self.gettlv(CORE_TLV_NODE_SESSION)
        if s is not None:
            for sid in s.split('|'):
                r.append(int(sid))
        return r


class CoreNodeMessage(CoreMessage):
    msgtype = CORE_API_NODE_MSG
    flagmap = message_flags
    tlvcls = CoreNodeTlv

class CoreLinkMessage(CoreMessage):
    msgtype = CORE_API_LINK_MSG
    flagmap = message_flags
    tlvcls = CoreLinkTlv

class CoreExecMessage(CoreMessage):
    msgtype = CORE_API_EXEC_MSG
    flagmap = message_flags
    tlvcls = CoreExecTlv

class CoreRegMessage(CoreMessage):
    msgtype = CORE_API_REG_MSG
    flagmap = message_flags
    tlvcls = CoreRegTlv

class CoreConfMessage(CoreMessage):
    msgtype = CORE_API_CONF_MSG
    flagmap = message_flags
    tlvcls = CoreConfTlv

class CoreFileMessage(CoreMessage):
    msgtype = CORE_API_FILE_MSG
    flagmap = message_flags
    tlvcls = CoreFileTlv

class CoreIfaceMessage(CoreMessage):
    msgtype = CORE_API_IFACE_MSG
    flagmap = message_flags
    tlvcls = CoreIfaceTlv

class CoreEventMessage(CoreMessage):
    msgtype = CORE_API_EVENT_MSG
    flagmap = message_flags
    tlvcls = CoreEventTlv

class CoreSessionMessage(CoreMessage):
    msgtype = CORE_API_SESS_MSG
    flagmap = message_flags
    tlvcls = CoreSessionTlv

class CoreExceptionMessage(CoreMessage):
    msgtype = CORE_API_EXCP_MSG
    flagmap = message_flags
    tlvcls = CoreExceptionTlv

msgclsmap = {
    CORE_API_NODE_MSG: CoreNodeMessage,
    CORE_API_LINK_MSG: CoreLinkMessage,
    CORE_API_EXEC_MSG: CoreExecMessage,
    CORE_API_REG_MSG: CoreRegMessage,
    CORE_API_CONF_MSG: CoreConfMessage,
    CORE_API_FILE_MSG: CoreFileMessage,
    CORE_API_IFACE_MSG: CoreIfaceMessage,
    CORE_API_EVENT_MSG: CoreEventMessage,
    CORE_API_SESS_MSG: CoreSessionMessage,
    CORE_API_EXCP_MSG: CoreExceptionMessage,
}

def msg_class(msgtypeid):
    global msgclsmap
    return msgclsmap[msgtypeid]

nodeclsmap = {}

def add_node_class(name, nodetypeid, nodecls, change = False):
    global nodeclsmap
    if nodetypeid in nodeclsmap:
        if not change:
            raise ValueError("node class already exists for nodetypeid %s" % nodetypeid)
    nodeclsmap[nodetypeid] = nodecls
    if nodetypeid not in node_types:
        node_types[nodetypeid] = name
        exec("%s = %s" % (name, nodetypeid), globals())
    elif name != node_types[nodetypeid]:
        raise ValueError("node type already exists for '%s'" % name)
    else:
        pass

def change_node_class(name, nodetypeid, nodecls):
    return add_node_class(name, nodetypeid, nodecls, change = True)

def node_class(nodetypeid):
    global nodeclsmap
    return nodeclsmap[nodetypeid]

def str_to_list(s):
    ''' Helper to convert pipe-delimited string ("a|b|c") into a list (a, b, c)
    '''
    if s is None:
        return None
    return s.split("|")

def state_name(n):
    ''' Helper to convert state number into state name using event types.
    '''
    if n in event_types:
        eventname = event_types[n]
        name = eventname.split('_')[2]
    else:
        name = "unknown"
    return name
