# Export from BRITE topology
# Generator Model Used: Model (5 - TopDown)
Model (3 - ASWaxman):  10 1000 100 1  2  0.15000000596046448 0.20000000298023224 1 1 10.0 1024.0 
Model (1 - RTWaxman):  10 1000 100 1  2  0.15000000596046448 0.20000000298023224 1 1 10.0 1024.0 




proc create_topology{} {
	global ns

	#nodes:
	set num_node 100
	for {set i 0} {$i < $num_node} {incr i} {
	   set n($i) [$ns node]
	}

	 #links:
	set qtype DropTail

	$ns duplex-link $n(0) $n(7) 10.0Mb 2.567067754167381ms $qtype
	$ns duplex-link $n(0) $n(6) 10.0Mb 0.8389982466980022ms $qtype
	$ns duplex-link $n(1) $n(7) 10.0Mb 1.5301687070244878ms $qtype
	$ns duplex-link $n(1) $n(9) 10.0Mb 2.593378788535563ms $qtype
	$ns duplex-link $n(1) $n(18) 10.0Mb 2.538126878929145ms $qtype
	$ns duplex-link $n(2) $n(7) 10.0Mb 2.7789713041082225ms $qtype
	$ns duplex-link $n(2) $n(0) 10.0Mb 1.6158589833392714ms $qtype
	$ns duplex-link $n(3) $n(1) 10.0Mb 0.2369244506755372ms $qtype
	$ns duplex-link $n(3) $n(2) 10.0Mb 1.5809002759213493ms $qtype
	$ns duplex-link $n(4) $n(0) 10.0Mb 0.3725330072511264ms $qtype
	$ns duplex-link $n(4) $n(9) 10.0Mb 0.9356220166823485ms $qtype
	$ns duplex-link $n(5) $n(6) 10.0Mb 1.4479602044334485ms $qtype
	$ns duplex-link $n(5) $n(9) 10.0Mb 0.7471388981455191ms $qtype
	$ns duplex-link $n(6) $n(3) 10.0Mb 2.5027200918302954ms $qtype
	$ns duplex-link $n(6) $n(2) 10.0Mb 1.1695596290532595ms $qtype
	$ns duplex-link $n(7) $n(3) 10.0Mb 1.7411822113820306ms $qtype
	$ns duplex-link $n(7) $n(5) 10.0Mb 2.371643062596767ms $qtype
	$ns duplex-link $n(8) $n(9) 10.0Mb 1.0537352594167797ms $qtype
	$ns duplex-link $n(8) $n(7) 10.0Mb 1.1938146660177533ms $qtype
	$ns duplex-link $n(9) $n(7) 10.0Mb 1.8723615560606186ms $qtype
	$ns duplex-link $n(9) $n(6) 10.0Mb 2.1170627536268416ms $qtype
	$ns duplex-link $n(9) $n(70) 10.0Mb 1.2401094822537364ms $qtype
	$ns duplex-link $n(10) $n(16) 10.0Mb 0.57583056814009ms $qtype
	$ns duplex-link $n(10) $n(17) 10.0Mb 1.8348966428975144ms $qtype
	$ns duplex-link $n(11) $n(16) 10.0Mb 1.4365773388400682ms $qtype
	$ns duplex-link $n(11) $n(15) 10.0Mb 2.362408685147645ms $qtype
	$ns duplex-link $n(12) $n(10) 10.0Mb 1.6279602415341092ms $qtype
	$ns duplex-link $n(12) $n(13) 10.0Mb 1.749825866408824ms $qtype
	$ns duplex-link $n(13) $n(10) 10.0Mb 0.3718005419093705ms $qtype
	$ns duplex-link $n(13) $n(11) 10.0Mb 1.67767818362029ms $qtype
	$ns duplex-link $n(13) $n(72) 10.0Mb 1.7384706557080227ms $qtype
	$ns duplex-link $n(14) $n(13) 10.0Mb 0.5898050864693893ms $qtype
	$ns duplex-link $n(14) $n(10) 10.0Mb 0.2854848798201536ms $qtype
	$ns duplex-link $n(15) $n(13) 10.0Mb 0.7911096826797153ms $qtype
	$ns duplex-link $n(15) $n(10) 10.0Mb 0.8650378848338032ms $qtype
	$ns duplex-link $n(16) $n(17) 10.0Mb 1.2695871888935533ms $qtype
	$ns duplex-link $n(16) $n(13) 10.0Mb 0.24486876387307852ms $qtype
	$ns duplex-link $n(17) $n(15) 10.0Mb 1.7973503199838574ms $qtype
	$ns duplex-link $n(17) $n(13) 10.0Mb 1.4673218770830598ms $qtype
	$ns duplex-link $n(18) $n(19) 10.0Mb 1.7394048289347595ms $qtype
	$ns duplex-link $n(18) $n(16) 10.0Mb 1.4087703521095405ms $qtype
	$ns duplex-link $n(18) $n(54) 10.0Mb 1.9900669861884674ms $qtype
	$ns duplex-link $n(19) $n(11) 10.0Mb 0.8640919780991726ms $qtype
	$ns duplex-link $n(19) $n(10) 10.0Mb 1.270638418409094ms $qtype
	$ns duplex-link $n(20) $n(26) 10.0Mb 0.8804638967920476ms $qtype
	$ns duplex-link $n(20) $n(22) 10.0Mb 2.4831264935821404ms $qtype
	$ns duplex-link $n(21) $n(29) 10.0Mb 0.24908104529560207ms $qtype
	$ns duplex-link $n(21) $n(23) 10.0Mb 1.2732190014557119ms $qtype
	$ns duplex-link $n(22) $n(24) 10.0Mb 0.5416181194149033ms $qtype
	$ns duplex-link $n(22) $n(25) 10.0Mb 1.2152083802358689ms $qtype
	$ns duplex-link $n(23) $n(22) 10.0Mb 0.24820844788944804ms $qtype
	$ns duplex-link $n(23) $n(24) 10.0Mb 0.5632592981772505ms $qtype
	$ns duplex-link $n(24) $n(21) 10.0Mb 1.1169666547632129ms $qtype
	$ns duplex-link $n(24) $n(27) 10.0Mb 3.0101844881983593ms $qtype
	$ns duplex-link $n(25) $n(23) 10.0Mb 1.0980745599661008ms $qtype
	$ns duplex-link $n(25) $n(26) 10.0Mb 1.411665950710108ms $qtype
	$ns duplex-link $n(26) $n(23) 10.0Mb 1.3624164033112083ms $qtype
	$ns duplex-link $n(26) $n(22) 10.0Mb 1.6105378181443974ms $qtype
	$ns duplex-link $n(27) $n(28) 10.0Mb 0.6933801909636362ms $qtype
	$ns duplex-link $n(27) $n(29) 10.0Mb 2.134990013591234ms $qtype
	$ns duplex-link $n(28) $n(22) 10.0Mb 3.690060247066546ms $qtype
	$ns duplex-link $n(28) $n(25) 10.0Mb 3.1736866394504832ms $qtype
	$ns duplex-link $n(29) $n(25) 10.0Mb 2.2142350461270968ms $qtype
	$ns duplex-link $n(29) $n(24) 10.0Mb 1.3411184942467516ms $qtype
	$ns duplex-link $n(29) $n(5) 10.0Mb 0.8995414127570747ms $qtype
	$ns duplex-link $n(29) $n(10) 10.0Mb 1.2539259548360941ms $qtype
	$ns duplex-link $n(30) $n(39) 10.0Mb 1.4737116917542927ms $qtype
	$ns duplex-link $n(30) $n(38) 10.0Mb 2.8189718574043523ms $qtype
	$ns duplex-link $n(31) $n(30) 10.0Mb 0.20761518049390604ms $qtype
	$ns duplex-link $n(31) $n(32) 10.0Mb 2.5783986730959922ms $qtype
	$ns duplex-link $n(32) $n(38) 10.0Mb 1.0637504909547775ms $qtype
	$ns duplex-link $n(32) $n(39) 10.0Mb 1.4915388545312547ms $qtype
	$ns duplex-link $n(32) $n(14) 10.0Mb 0.3651879457465521ms $qtype
	$ns duplex-link $n(33) $n(32) 10.0Mb 1.0984848591538026ms $qtype
	$ns duplex-link $n(33) $n(39) 10.0Mb 2.5045866162945716ms $qtype
	$ns duplex-link $n(34) $n(36) 10.0Mb 0.4381894797609511ms $qtype
	$ns duplex-link $n(34) $n(33) 10.0Mb 1.317557064211966ms $qtype
	$ns duplex-link $n(35) $n(39) 10.0Mb 0.4738019367936122ms $qtype
	$ns duplex-link $n(35) $n(38) 10.0Mb 1.5085249507859202ms $qtype
	$ns duplex-link $n(36) $n(32) 10.0Mb 1.5887773757408687ms $qtype
	$ns duplex-link $n(36) $n(30) 10.0Mb 2.8236826207413728ms $qtype
	$ns duplex-link $n(37) $n(36) 10.0Mb 0.23191701901678524ms $qtype
	$ns duplex-link $n(37) $n(33) 10.0Mb 0.9334134273690228ms $qtype
	$ns duplex-link $n(38) $n(37) 10.0Mb 2.8253193916162243ms $qtype
	$ns duplex-link $n(38) $n(33) 10.0Mb 2.0656480096957517ms $qtype
	$ns duplex-link $n(38) $n(7) 10.0Mb 3.4692975113640308ms $qtype
	$ns duplex-link $n(39) $n(31) 10.0Mb 1.6571120476118477ms $qtype
	$ns duplex-link $n(39) $n(36) 10.0Mb 2.641060999181983ms $qtype
	$ns duplex-link $n(40) $n(43) 10.0Mb 1.4182594606891548ms $qtype
	$ns duplex-link $n(40) $n(46) 10.0Mb 1.4899826857526446ms $qtype
	$ns duplex-link $n(40) $n(7) 10.0Mb 1.011760991820919ms $qtype
	$ns duplex-link $n(41) $n(48) 10.0Mb 3.2116801060579543ms $qtype
	$ns duplex-link $n(41) $n(47) 10.0Mb 1.1812220042364427ms $qtype
	$ns duplex-link $n(42) $n(40) 10.0Mb 1.6757604155939134ms $qtype
	$ns duplex-link $n(42) $n(43) 10.0Mb 0.5145651891054035ms $qtype
	$ns duplex-link $n(42) $n(39) 10.0Mb 1.3332094126749536ms $qtype
	$ns duplex-link $n(43) $n(45) 10.0Mb 1.5323812550401283ms $qtype
	$ns duplex-link $n(43) $n(44) 10.0Mb 1.5903173299416307ms $qtype
	$ns duplex-link $n(44) $n(41) 10.0Mb 1.0919372356356467ms $qtype
	$ns duplex-link $n(44) $n(40) 10.0Mb 2.3906750699184323ms $qtype
	$ns duplex-link $n(45) $n(40) 10.0Mb 0.446053901477734ms $qtype
	$ns duplex-link $n(45) $n(41) 10.0Mb 2.6806788805304027ms $qtype
	$ns duplex-link $n(46) $n(48) 10.0Mb 1.1314905156465502ms $qtype
	$ns duplex-link $n(46) $n(49) 10.0Mb 0.9312414188537529ms $qtype
	$ns duplex-link $n(47) $n(43) 10.0Mb 1.4640766144527053ms $qtype
	$ns duplex-link $n(47) $n(49) 10.0Mb 0.45757894132943866ms $qtype
	$ns duplex-link $n(48) $n(43) 10.0Mb 2.5355172091460085ms $qtype
	$ns duplex-link $n(48) $n(40) 10.0Mb 1.76262350631607ms $qtype
	$ns duplex-link $n(49) $n(42) 10.0Mb 1.3757446630279935ms $qtype
	$ns duplex-link $n(49) $n(44) 10.0Mb 0.5204134415481707ms $qtype
	$ns duplex-link $n(50) $n(55) 10.0Mb 0.8850958430962331ms $qtype
	$ns duplex-link $n(50) $n(56) 10.0Mb 0.475595027197657ms $qtype
	$ns duplex-link $n(51) $n(56) 10.0Mb 0.9637289597133614ms $qtype
	$ns duplex-link $n(51) $n(54) 10.0Mb 1.6398059773844895ms $qtype
	$ns duplex-link $n(52) $n(57) 10.0Mb 0.5723711055813593ms $qtype
	$ns duplex-link $n(52) $n(54) 10.0Mb 1.849428671458802ms $qtype
	$ns duplex-link $n(53) $n(59) 10.0Mb 0.862771124922729ms $qtype
	$ns duplex-link $n(53) $n(56) 10.0Mb 2.302046632667692ms $qtype
	$ns duplex-link $n(54) $n(58) 10.0Mb 0.8640082766432589ms $qtype
	$ns duplex-link $n(54) $n(59) 10.0Mb 2.8780319160475547ms $qtype
	$ns duplex-link $n(54) $n(5) 10.0Mb 1.609826078978051ms $qtype
	$ns duplex-link $n(55) $n(59) 10.0Mb 0.966668517681253ms $qtype
	$ns duplex-link $n(55) $n(58) 10.0Mb 1.9540024120638528ms $qtype
	$ns duplex-link $n(56) $n(54) 10.0Mb 0.9872708352342282ms $qtype
	$ns duplex-link $n(56) $n(59) 10.0Mb 2.1809404173716653ms $qtype
	$ns duplex-link $n(57) $n(54) 10.0Mb 2.2895354499510616ms $qtype
	$ns duplex-link $n(57) $n(55) 10.0Mb 1.6209979556977316ms $qtype
	$ns duplex-link $n(58) $n(53) 10.0Mb 3.355132526981048ms $qtype
	$ns duplex-link $n(58) $n(56) 10.0Mb 1.5725875642035245ms $qtype
	$ns duplex-link $n(59) $n(52) 10.0Mb 1.660238006089112ms $qtype
	$ns duplex-link $n(59) $n(57) 10.0Mb 1.9720381527543038ms $qtype
	$ns duplex-link $n(59) $n(41) 10.0Mb 3.094964350774594ms $qtype
	$ns duplex-link $n(60) $n(68) 10.0Mb 1.9725176757164684ms $qtype
	$ns duplex-link $n(60) $n(63) 10.0Mb 1.3552106164817723ms $qtype
	$ns duplex-link $n(60) $n(49) 10.0Mb 2.8331081400756584ms $qtype
	$ns duplex-link $n(61) $n(64) 10.0Mb 0.5246296258942909ms $qtype
	$ns duplex-link $n(61) $n(67) 10.0Mb 0.7053362457461366ms $qtype
	$ns duplex-link $n(62) $n(69) 10.0Mb 0.9062697677165996ms $qtype
	$ns duplex-link $n(62) $n(68) 10.0Mb 1.188317114931586ms $qtype
	$ns duplex-link $n(63) $n(61) 10.0Mb 1.3256980310534268ms $qtype
	$ns duplex-link $n(63) $n(66) 10.0Mb 1.8973581975633704ms $qtype
	$ns duplex-link $n(64) $n(63) 10.0Mb 1.6489844873395976ms $qtype
	$ns duplex-link $n(64) $n(60) 10.0Mb 2.619805693322836ms $qtype
	$ns duplex-link $n(65) $n(61) 10.0Mb 0.587678974780486ms $qtype
	$ns duplex-link $n(65) $n(64) 10.0Mb 0.14619852111697304ms $qtype
	$ns duplex-link $n(66) $n(61) 10.0Mb 0.8210082401887587ms $qtype
	$ns duplex-link $n(66) $n(60) 10.0Mb 2.205451536316714ms $qtype
	$ns duplex-link $n(67) $n(60) 10.0Mb 1.6688475371664995ms $qtype
	$ns duplex-link $n(67) $n(66) 10.0Mb 0.5661556571720594ms $qtype
	$ns duplex-link $n(67) $n(37) 10.0Mb 1.643086758515356ms $qtype
	$ns duplex-link $n(68) $n(67) 10.0Mb 0.8115553426479176ms $qtype
	$ns duplex-link $n(68) $n(61) 10.0Mb 1.4196238656874427ms $qtype
	$ns duplex-link $n(69) $n(61) 10.0Mb 1.8982376247533086ms $qtype
	$ns duplex-link $n(69) $n(67) 10.0Mb 1.637096422333942ms $qtype
	$ns duplex-link $n(70) $n(74) 10.0Mb 2.8895142569512737ms $qtype
	$ns duplex-link $n(70) $n(77) 10.0Mb 0.592440258745229ms $qtype
	$ns duplex-link $n(71) $n(76) 10.0Mb 0.27687829250790735ms $qtype
	$ns duplex-link $n(71) $n(75) 10.0Mb 1.344300549743682ms $qtype
	$ns duplex-link $n(72) $n(73) 10.0Mb 0.32247212939845077ms $qtype
	$ns duplex-link $n(72) $n(76) 10.0Mb 0.9697999617867403ms $qtype
	$ns duplex-link $n(73) $n(70) 10.0Mb 0.8672730621856108ms $qtype
	$ns duplex-link $n(73) $n(77) 10.0Mb 0.3388919278853577ms $qtype
	$ns duplex-link $n(73) $n(24) 10.0Mb 2.260070905487098ms $qtype
	$ns duplex-link $n(74) $n(71) 10.0Mb 0.9558866839389447ms $qtype
	$ns duplex-link $n(74) $n(78) 10.0Mb 0.837783927012057ms $qtype
	$ns duplex-link $n(75) $n(72) 10.0Mb 2.1572933896336752ms $qtype
	$ns duplex-link $n(75) $n(73) 10.0Mb 2.285108825759166ms $qtype
	$ns duplex-link $n(76) $n(74) 10.0Mb 1.2327122782929147ms $qtype
	$ns duplex-link $n(76) $n(77) 10.0Mb 1.2515411976481647ms $qtype
	$ns duplex-link $n(77) $n(75) 10.0Mb 2.5625908290886037ms $qtype
	$ns duplex-link $n(77) $n(74) 10.0Mb 2.4840516153777954ms $qtype
	$ns duplex-link $n(78) $n(72) 10.0Mb 1.9589614706085798ms $qtype
	$ns duplex-link $n(78) $n(75) 10.0Mb 1.8303795937680494ms $qtype
	$ns duplex-link $n(78) $n(39) 10.0Mb 2.104292471967304ms $qtype
	$ns duplex-link $n(79) $n(73) 10.0Mb 1.3263021848808247ms $qtype
	$ns duplex-link $n(79) $n(71) 10.0Mb 1.3798631846751164ms $qtype
	$ns duplex-link $n(80) $n(82) 10.0Mb 1.3997972643255252ms $qtype
	$ns duplex-link $n(80) $n(84) 10.0Mb 0.781209674636336ms $qtype
	$ns duplex-link $n(81) $n(86) 10.0Mb 0.6570789357079149ms $qtype
	$ns duplex-link $n(81) $n(87) 10.0Mb 1.383748344700969ms $qtype
	$ns duplex-link $n(82) $n(86) 10.0Mb 1.2261963139101895ms $qtype
	$ns duplex-link $n(82) $n(87) 10.0Mb 1.0604872923129802ms $qtype
	$ns duplex-link $n(82) $n(78) 10.0Mb 1.5705485610972703ms $qtype
	$ns duplex-link $n(83) $n(87) 10.0Mb 0.28045183626146986ms $qtype
	$ns duplex-link $n(83) $n(88) 10.0Mb 1.5504452412464758ms $qtype
	$ns duplex-link $n(84) $n(87) 10.0Mb 0.898730872782038ms $qtype
	$ns duplex-link $n(84) $n(85) 10.0Mb 2.468383319695678ms $qtype
	$ns duplex-link $n(85) $n(83) 10.0Mb 2.331250323816243ms $qtype
	$ns duplex-link $n(85) $n(88) 10.0Mb 0.953835847687894ms $qtype
	$ns duplex-link $n(86) $n(88) 10.0Mb 0.5761782686154678ms $qtype
	$ns duplex-link $n(86) $n(89) 10.0Mb 1.2345026455122083ms $qtype
	$ns duplex-link $n(87) $n(86) 10.0Mb 1.233745326103597ms $qtype
	$ns duplex-link $n(87) $n(89) 10.0Mb 2.2804174687945626ms $qtype
	$ns duplex-link $n(87) $n(24) 10.0Mb 1.9006978561833368ms $qtype
	$ns duplex-link $n(88) $n(81) 10.0Mb 1.1745861781941782ms $qtype
	$ns duplex-link $n(88) $n(80) 10.0Mb 2.2121738424088258ms $qtype
	$ns duplex-link $n(89) $n(82) 10.0Mb 2.4572356282386942ms $qtype
	$ns duplex-link $n(89) $n(85) 10.0Mb 0.5226854644653949ms $qtype
	$ns duplex-link $n(90) $n(93) 10.0Mb 2.273294983685452ms $qtype
	$ns duplex-link $n(90) $n(92) 10.0Mb 2.3722505306161388ms $qtype
	$ns duplex-link $n(91) $n(92) 10.0Mb 1.2216144595091838ms $qtype
	$ns duplex-link $n(91) $n(93) 10.0Mb 1.7138216781424203ms $qtype
	$ns duplex-link $n(92) $n(94) 10.0Mb 0.3965346213403029ms $qtype
	$ns duplex-link $n(92) $n(96) 10.0Mb 1.6973300084653047ms $qtype
	$ns duplex-link $n(93) $n(95) 10.0Mb 0.39531215560962796ms $qtype
	$ns duplex-link $n(93) $n(99) 10.0Mb 2.0658203687629513ms $qtype
	$ns duplex-link $n(94) $n(91) 10.0Mb 1.614991138024283ms $qtype
	$ns duplex-link $n(94) $n(96) 10.0Mb 1.6195730531975403ms $qtype
	$ns duplex-link $n(95) $n(92) 10.0Mb 0.5540076876383492ms $qtype
	$ns duplex-link $n(95) $n(94) 10.0Mb 0.16880452581472205ms $qtype
	$ns duplex-link $n(96) $n(90) 10.0Mb 1.3507657339150136ms $qtype
	$ns duplex-link $n(96) $n(91) 10.0Mb 2.2511252031586793ms $qtype
	$ns duplex-link $n(96) $n(27) 10.0Mb 2.715895987808858ms $qtype
	$ns duplex-link $n(97) $n(99) 10.0Mb 1.921343665895109ms $qtype
	$ns duplex-link $n(97) $n(98) 10.0Mb 2.630230622402534ms $qtype
	$ns duplex-link $n(97) $n(81) 10.0Mb 1.3218316417090488ms $qtype
	$ns duplex-link $n(98) $n(91) 10.0Mb 0.797804151759987ms $qtype
	$ns duplex-link $n(98) $n(92) 10.0Mb 0.9917573541705647ms $qtype
	$ns duplex-link $n(99) $n(92) 10.0Mb 2.1269256211496446ms $qtype
	$ns duplex-link $n(99) $n(90) 10.0Mb 0.26903138505811525ms $qtype

}   #end function create_topology

#-------------  extract_leaf_nodes:  array with smallest degree nodes -----
proc extract_leaf_nodes{} {

	# minimum degree in this graph is: 2. 
	set leaf(0)  14
	set leaf(1)  18
	set leaf(2)  22
	set leaf(3)  30
	set leaf(4)  44
	set leaf(5)  45
	set leaf(6)  60
	set leaf(7)  61
	set leaf(8)  72
	set leaf(9)  75
	set leaf(10)  89

}  #end function extract_leaf_nodes

#----------  extract_nonleaf_nodes:  array with nodes which have degree > 2  ---
proc extract_nonleaf_nodes{} {
	set non_leaf(0) 10	#deg=4
	set non_leaf(1) 11	#deg=4
	set non_leaf(2) 12	#deg=4
	set non_leaf(3) 13	#deg=4
	set non_leaf(4) 15	#deg=5
	set non_leaf(5) 16	#deg=5
	set non_leaf(6) 17	#deg=9
	set non_leaf(7) 19	#deg=7
	set non_leaf(8) 20	#deg=8
	set non_leaf(9) 21	#deg=4
	set non_leaf(10) 23	#deg=8
	set non_leaf(11) 24	#deg=3
	set non_leaf(12) 25	#deg=4
	set non_leaf(13) 26	#deg=5
	set non_leaf(14) 27	#deg=4
	set non_leaf(15) 28	#deg=4
	set non_leaf(16) 29	#deg=3
	set non_leaf(17) 31	#deg=3
	set non_leaf(18) 32	#deg=6
	set non_leaf(19) 33	#deg=5
	set non_leaf(20) 34	#deg=7
	set non_leaf(21) 35	#deg=5
	set non_leaf(22) 36	#deg=4
	set non_leaf(23) 37	#deg=4
	set non_leaf(24) 38	#deg=3
	set non_leaf(25) 39	#deg=6
	set non_leaf(26) 40	#deg=4
	set non_leaf(27) 41	#deg=3
	set non_leaf(28) 42	#deg=6
	set non_leaf(29) 43	#deg=5
	set non_leaf(30) 46	#deg=5
	set non_leaf(31) 47	#deg=4
	set non_leaf(32) 48	#deg=6
	set non_leaf(33) 49	#deg=8
	set non_leaf(34) 50	#deg=7
	set non_leaf(35) 51	#deg=5
	set non_leaf(36) 52	#deg=4
	set non_leaf(37) 53	#deg=6
	set non_leaf(38) 54	#deg=4
	set non_leaf(39) 55	#deg=3
	set non_leaf(40) 56	#deg=3
	set non_leaf(41) 57	#deg=3
	set non_leaf(42) 58	#deg=4
	set non_leaf(43) 59	#deg=5
	set non_leaf(44) 62	#deg=3
	set non_leaf(45) 63	#deg=3
	set non_leaf(46) 64	#deg=8
	set non_leaf(47) 65	#deg=4
	set non_leaf(48) 66	#deg=6
	set non_leaf(49) 67	#deg=4
	set non_leaf(50) 68	#deg=4
	set non_leaf(51) 69	#deg=7
	set non_leaf(52) 70	#deg=6
	set non_leaf(53) 71	#deg=7
	set non_leaf(54) 73	#deg=4
	set non_leaf(55) 74	#deg=4
	set non_leaf(56) 76	#deg=4
	set non_leaf(57) 77	#deg=6
	set non_leaf(58) 78	#deg=4
	set non_leaf(59) 79	#deg=3
	set non_leaf(60) 80	#deg=4
	set non_leaf(61) 81	#deg=4
	set non_leaf(62) 82	#deg=5
	set non_leaf(63) 83	#deg=6
	set non_leaf(64) 84	#deg=5
	set non_leaf(65) 85	#deg=5
	set non_leaf(66) 86	#deg=4
	set non_leaf(67) 87	#deg=5
	set non_leaf(68) 88	#deg=5
	set non_leaf(69) 90	#deg=3
	set non_leaf(70) 91	#deg=4
	set non_leaf(71) 92	#deg=5
	set non_leaf(72) 93	#deg=3
	set non_leaf(73) 94	#deg=3
	set non_leaf(74) 95	#deg=4
	set non_leaf(75) 96	#deg=5
	set non_leaf(76) 97	#deg=7
	set non_leaf(77) 98	#deg=5
	set non_leaf(78) 99	#deg=4
	set non_leaf(79) 100	#deg=4
	set non_leaf(80) 101	#deg=5
	set non_leaf(81) 102	#deg=7
	set non_leaf(82) 103	#deg=4
	set non_leaf(83) 104	#deg=4
	set non_leaf(84) 105	#deg=3
	set non_leaf(85) 106	#deg=5
	set non_leaf(86) 107	#deg=3
	set non_leaf(87) 108	#deg=3
	set non_leaf(88) 109	#deg=4

}  #end function extract_nonleaf_nodes
