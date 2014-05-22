# brite.tcl enthaelt alle Bestandteile fuer Brite integration in core.
# -baut GUI auf
# -erstellt GUI_GEN äquivalent
# -ruft cppgen oder java Brite auf und erstellt Topologie in ns2(?) Format

proc doStuff1 {} {

  # mit http://community.activestate.com/node/10009 dem hier super
  # konkret bei jedem combomenu mit welchem sich etwas aendert wird disabled und enabled.

  # fenster initalisierung
  set wi .core_testing
  catch { destroy $wi }
  toplevel $wi

  wm transient $wi .
  wm resizable $wi 0 0
  wm title $wi "Topology Parameter"

  # globale g_prefs verfuegbar machen und bisherige einstellungen
  #   darin vorruebergehend sichern falls man dieses
  #   fenster abbricht
  global testing_prefs testing_prefs_old
  array set testing_prefs_old [array get testing_prefs]


  # dropdownmenue eintraege definition
  #immer der entsprechende wert aus brite als
  #  standart eintrag ausgeawaehlt: variable vordefinieren
  set TOPOTYPES {{1 Level: AS ONLY} {1 Level: ROUTER (IP) ONLY} {2 Level: TOP-DOWN} {2 Level: BOTTOM-UP}}
  set MODELS {{Waxman} {BA} {BA-2} {GLP}}
  set NODEPLACEM {{Random} {Heavy Tailed}}
  set GROWTHTYPE {{All} {Incremental}}
  set PREFCONN {{None} {On}}
  set CONNLOCALI {{Off} {On}}
  set BANDWIDTHD {{Constant} {Uniform} {Exponential} {Heavy Tailed}}
  set EDGCONMOD {{Random} {Smallest-Degree} {Smallest-Degree NonLeaf} {Smallest k-Degree}}
  set INTEBWDIST {{Constant} {Uniform} {Exponential} {Heavy Tailed}}
  set INTABWDIST {{Constant} {Uniform} {Exponential} {Heavy Tailed}}
  set EXECUTABLE {{Java} {C++}}

  #
  # Top
  #
  labelframe $wi.top -borderwidth 4
  frame $wi.top.line1
  label $wi.top.line1.label -text "Topology Type"
#  set topotypes [linsert $TOPOTYPES 0 "TOPOTYPES"]
  set topotypes $TOPOTYPES
  ttk::combobox $wi.top.line1.combo -width 20 -exportselection 0 \
    -values $topotypes -textvariable testing_prefs(gui_brite_top_topotypes)
# -selectioncommand {[switch_top_topotypes $wi.top.line1.combo get]}
# -modifycmd {after 0 {switch_top_topotypes $wi.top.line1.combo}}

  label $wi.top.line1.label2 -text "Executable:"
  set executables $EXECUTABLE
  ttk::combobox $wi.top.line1.combo2 -width 15 -exportselection 0 \
    -values $executables -textvariable testing_prefs(gui_brite_top_executables)

#; zurueck_stellen; destroy $wi"
  button $wi.top.line1.cancel -text "Cancel" -command {
    # im falle eines abbruchs die bisherigen einstellungen wieder herstellen
    global testing_prefs testing_prefs_old
    array set testing_prefs [array get testing_prefs_old]
    destroy .core_testing
  }

  button $wi.top.line1.save -text "Save & Close" -command "writeBriteConf; destroy .core_testing"

  pack $wi.top.line1.label $wi.top.line1.combo $wi.top.line1.label2 $wi.top.line1.combo2 $wi.top.line1.cancel $wi.top.line1.save  -side left
  pack $wi.top.line1 -side top -anchor w -padx 4 -pady 4
  pack $wi.top -side top -fill x

  # combobox wurde verstellt. sichtbarkeiten anhand dessen einstellen
  bind $wi.top.line1.combo <<ComboboxSelected>> {
    switched
  }

  #
  # AS
  #
  labelframe $wi.as -borderwidth 4 -text "AS"

  frame $wi.as.line1
  label $wi.as.line1.label -text "AS Topology Parameters"
  # fkt importAS bei bedarf erstellen & button wieder einkommentieren
  #button $wi.as.line1.import -text "Import..." -command "importAS"
  #$wi.as.line1.import
  pack $wi.as.line1.label -side left
  pack $wi.as.line1 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line2
  label $wi.as.line2.label_hs -text "HS:"
  entry $wi.as.line2.entry_hs -bg white -width 8 -textvariable testing_prefs(gui_brite_as_hs)
  label $wi.as.line2.label_n -text "N:"
  entry $wi.as.line2.entry_n -bg white -width 8 -textvariable testing_prefs(gui_brite_as_n)
  pack $wi.as.line2.label_hs $wi.as.line2.entry_hs $wi.as.line2.label_n $wi.as.line2.entry_n -side left
  pack $wi.as.line2 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line3
  label $wi.as.line3.label_ls -text "LS:"
  entry $wi.as.line3.entry_ls -bg white -width 8 -textvariable testing_prefs(gui_brite_as_ls)
  label $wi.as.line3.label_model -text "Model:"
#  set models [linsert $MODELS 0 "MODEL"]
  set models $MODELS
  ttk::combobox $wi.as.line3.combo -width 10 -exportselection 0 \
    -values $models -textvariable testing_prefs(gui_brite_as_models)
  pack $wi.as.line3.label_ls $wi.as.line3.entry_ls $wi.as.line3.label_model $wi.as.line3.combo -side left
  pack $wi.as.line3 -side top -anchor w -padx 4 -pady 4

  bind $wi.as.line3.combo <<ComboboxSelected>> {
    switched
  }


  frame $wi.as.line4
  label $wi.as.line4.label_line4 -text "Model Specific Parameters"
  pack $wi.as.line4.label_line4
  pack $wi.as.line4 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line5
  label $wi.as.line5.label_np -text "Node Placement:"
#  set np [linsert $NODEPLACEM 0 "NODEPLACEMENT"]
  set np $NODEPLACEM
  ttk::combobox $wi.as.line5.combo -width 10 -exportselection 0 \
    -values $np -textvariable testing_prefs(gui_brite_as_nodeplacement)
  label $wi.as.line5.label_alpha -text "alpha:"
  entry $wi.as.line5.entry_alpha -bg white -width 8 -textvariable testing_prefs(gui_brite_as_alpha)
  label $wi.as.line5.label_p -text "p (add):"
  entry $wi.as.line5.entry_p -bg white -width 8 -textvariable testing_prefs(gui_brite_as_p)
  pack $wi.as.line5.label_np $wi.as.line5.combo $wi.as.line5.label_alpha $wi.as.line5.entry_alpha $wi.as.line5.label_p $wi.as.line5.entry_p -side left
  pack $wi.as.line5 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line6
  label $wi.as.line6.label_gt -text "Growth Type:"
#  set gt [linsert $GROWTHTYPE 0 "GROWTHTYPE"]
  set gt $GROWTHTYPE
  ttk::combobox $wi.as.line6.combo -width 10 -exportselection 0 \
    -values $gt -textvariable testing_prefs(gui_brite_as_growthtype)
  label $wi.as.line6.label_beta -text "beta:"
  entry $wi.as.line6.entry_beta -bg white -width 8 -textvariable testing_prefs(gui_brite_as_beta)
  label $wi.as.line6.label_q -text "q (rewired):"
  entry $wi.as.line6.entry_q -bg white -width 8 -textvariable testing_prefs(gui_brite_as_q)
  pack $wi.as.line6.label_gt $wi.as.line6.combo $wi.as.line6.label_beta $wi.as.line6.entry_beta $wi.as.line6.label_q $wi.as.line6.entry_q -side left
  pack $wi.as.line6 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line7
  label $wi.as.line7.label_pc -text "Pref. Conn:"
#  set pc [linsert $PREFCONN 0 "PREF.CONN."]
  set pc $PREFCONN
  ttk::combobox $wi.as.line7.combo -width 10 -exportselection 0 \
    -values $pc -textvariable testing_prefs(gui_brite_as_prefconn)
  label $wi.as.line7.label_gamma -text "gamma:"
  entry $wi.as.line7.entry_gamma -bg white -width 8 -textvariable testing_prefs(gui_brite_as_gamma)
  pack $wi.as.line7.label_pc $wi.as.line7.combo $wi.as.line7.label_gamma $wi.as.line7.entry_gamma -side left
  pack $wi.as.line7 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line8
  label $wi.as.line8.label_cl -text "Conn. Locality:"
#  set cl [linsert $CONNLOCALI 0 "CONN.LOCALITY"]
  set cl $CONNLOCALI
  ttk::combobox $wi.as.line8.combo -width 10 -exportselection 0 \
    -values $cl -textvariable testing_prefs(gui_brite_as_connlocali)
  label $wi.as.line8.label_m -text "m:"
  entry $wi.as.line8.entry_m -bg white -width 8 -textvariable testing_prefs(gui_brite_as_m)
  pack $wi.as.line8.label_cl $wi.as.line8.combo $wi.as.line8.label_m $wi.as.line8.entry_m -side left
  pack $wi.as.line8 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line9
  label $wi.as.line9.label_bd -text "Bandwidth Distr:"
#  set bd [linsert $BANDWIDTHD 0 "BANDWIDTHDISTRIBUTION"]
  set bd $BANDWIDTHD
  ttk::combobox $wi.as.line9.combo -width 10 -exportselection 0 \
    -values $bd -textvariable testing_prefs(gui_brite_as_bandwidthd)
  label $wi.as.line9.label_maxBW -text "Max BW:"
  entry $wi.as.line9.entry_maxBW -bg white -width 8 -textvariable testing_prefs(gui_brite_as_maxBW)
  pack $wi.as.line9.label_bd $wi.as.line9.combo $wi.as.line9.label_maxBW $wi.as.line9.entry_maxBW -side left
  pack $wi.as.line9 -side top -anchor w -padx 4 -pady 4

  frame $wi.as.line10
  label $wi.as.line10.label_minBW -text "Min BW:"
  entry $wi.as.line10.entry_minBW -bg white -width 8 -textvariable testing_prefs(gui_brite_as_minBW)
  pack $wi.as.line10.label_minBW $wi.as.line10.entry_minBW -side right
  pack $wi.as.line10 -side top -anchor w -padx 4 -pady 4

  pack $wi.as -side right -fill x

  #
  # Router
  #
  labelframe $wi.router -borderwidth 4 -text "Router"

  frame $wi.router.line1
  label $wi.router.line1.label -text "Router Topology Parameters"
  # importRouter erstellen und button wieder einkommentieren
  button $wi.router.line1.import -text "Import..." -command "importRouter"
  pack $wi.router.line1.label $wi.router.line1.import -side left
  pack $wi.router.line1 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line2
  label $wi.router.line2.label_hs -text "HS:"
  entry $wi.router.line2.entry_hs -bg white -width 8 -textvariable testing_prefs(gui_brite_router_hs)
  label $wi.router.line2.label_n -text "N:"
  entry $wi.router.line2.entry_n -bg white -width 8 -textvariable testing_prefs(gui_brite_router_n)
  pack $wi.router.line2.label_hs $wi.router.line2.entry_hs $wi.router.line2.label_n $wi.router.line2.entry_n -side left
  pack $wi.router.line2 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line3
  label $wi.router.line3.label_ls -text "LS:"
  entry $wi.router.line3.entry_ls -bg white -width 8 -textvariable testing_prefs(gui_brite_router_ls)
  label $wi.router.line3.label_model -text "Model:"
#  set models [linsert $MODELS 0 "MODEL"]
  set models $MODELS
  ttk::combobox $wi.router.line3.combo -width 10 -exportselection 0 \
    -values $models -textvariable testing_prefs(gui_brite_router_models)
  pack $wi.router.line3.label_ls $wi.router.line3.entry_ls $wi.router.line3.label_model $wi.router.line3.combo -side left
  pack $wi.router.line3 -side top -anchor w -padx 4 -pady 4

  bind $wi.router.line3.combo <<ComboboxSelected>> {
    switched
  }


  frame $wi.router.line4
  label $wi.router.line4.label_line4 -text "Model Specific Parameters"
  pack $wi.router.line4.label_line4
  pack $wi.router.line4 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line5
  label $wi.router.line5.label_np -text "Node Placement:"
#  set np [linsert $NODEPLACEM 0 "NODEPLACEMENT"]
  set np $NODEPLACEM
  ttk::combobox $wi.router.line5.combo -width 10 -exportselection 0 \
    -values $np -textvariable testing_prefs(gui_brite_router_nodeplacement)
  label $wi.router.line5.label_alpha -text "alpha:"
  entry $wi.router.line5.entry_alpha -bg white -width 8 -textvariable testing_prefs(gui_brite_router_alpha)
  label $wi.router.line5.label_p -text "p (add):"
  entry $wi.router.line5.entry_p -bg white -width 8 -textvariable testing_prefs(gui_brite_router_p)
  pack $wi.router.line5.label_np $wi.router.line5.combo $wi.router.line5.label_alpha $wi.router.line5.entry_alpha $wi.router.line5.label_p $wi.router.line5.entry_p -side left
  pack $wi.router.line5 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line6
  label $wi.router.line6.label_gt -text "Growth Type:"
#  set gt [linsert $GROWTHTYPE 0 "GROWTHTYPE"]
  set gt $GROWTHTYPE
  ttk::combobox $wi.router.line6.combo -width 10 -exportselection 0 \
    -values $gt -textvariable testing_prefs(gui_brite_router_growthtype)
  label $wi.router.line6.label_beta -text "beta:"
  entry $wi.router.line6.entry_beta -bg white -width 8 -textvariable testing_prefs(gui_brite_router_beta)
  label $wi.router.line6.label_q -text "q (rewired):"
  entry $wi.router.line6.entry_q -bg white -width 8 -textvariable testing_prefs(gui_brite_router_q)
  pack $wi.router.line6.label_gt $wi.router.line6.combo $wi.router.line6.label_beta $wi.router.line6.entry_beta $wi.router.line6.label_q $wi.router.line6.entry_q -side left
  pack $wi.router.line6 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line7
  label $wi.router.line7.label_pc -text "Pref. Conn:"
#  set pc [linsert $PREFCONN 0 "PREF.CONN."]
  set pc $PREFCONN
  ttk::combobox $wi.router.line7.combo -width 10 -exportselection 0 \
    -values $pc -textvariable testing_prefs(gui_brite_router_prefconn)
  label $wi.router.line7.label_gamma -text "gamma:"
  entry $wi.router.line7.entry_gamma -bg white -width 8 -textvariable testing_prefs(gui_brite_router_gamma)
  pack $wi.router.line7.label_pc $wi.router.line7.combo $wi.router.line7.label_gamma $wi.router.line7.entry_gamma -side left
  pack $wi.router.line7 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line8
  label $wi.router.line8.label_cl -text "Conn. Locality:"
#  set cl [linsert $CONNLOCALI 0 "CONN.LOCALITY"]
  set cl $CONNLOCALI
  ttk::combobox $wi.router.line8.combo -width 10 -exportselection 0 \
    -values $cl -textvariable testing_prefs(gui_brite_router_connlocali)
  label $wi.router.line8.label_m -text "m:"
  entry $wi.router.line8.entry_m -bg white -width 8 -textvariable testing_prefs(gui_brite_router_m)
  pack $wi.router.line8.label_cl $wi.router.line8.combo $wi.router.line8.label_m $wi.router.line8.entry_m -side left
  pack $wi.router.line8 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line9
  label $wi.router.line9.label_bd -text "Bandwidth Distr:"
#  set bd [linsert $BANDWIDTHD 0 "BANDWIDTHDISTRIBUTION"]
  set bd $BANDWIDTHD
  ttk::combobox $wi.router.line9.combo -width 10 -exportselection 0 \
    -values $bd -textvariable testing_prefs(gui_brite_router_bandwidthd)
  label $wi.router.line9.label_maxBW -text "Max BW:"
  entry $wi.router.line9.entry_maxBW -bg white -width 8 -textvariable testing_prefs(gui_brite_router_maxBW)
  pack $wi.router.line9.label_bd $wi.router.line9.combo $wi.router.line9.label_maxBW $wi.router.line9.entry_maxBW -side left
  pack $wi.router.line9 -side top -anchor w -padx 4 -pady 4

  frame $wi.router.line10
  label $wi.router.line10.label_minBW -text "Min BW:"
  entry $wi.router.line10.entry_minBW -bg white -width 8 -textvariable testing_prefs(gui_brite_router_minBW)
  pack $wi.router.line10.label_minBW $wi.router.line10.entry_minBW -side right
  pack $wi.router.line10 -side top -anchor w -padx 4 -pady 4

  pack $wi.router -side right -fill x

  #
  # Top Down
  #
  labelframe $wi.topdown -borderwidth 4 -text "Top Down"

  frame $wi.topdown.line1
  label $wi.topdown.line1.label -text "Top Down Topology Parameters"
  pack $wi.topdown.line1.label -side right
  pack $wi.topdown.line1 -side top -anchor w -padx 4 -pady 4

  frame $wi.topdown.line2
  label $wi.topdown.line2.label_ecm -text "Edge Connection Model:"
#  set ecm [linsert $EDGCONMOD 0 "EdgeConnectionMod"]
  set ecm $EDGCONMOD
    ttk::combobox $wi.topdown.line2.combo -width 15 -exportselection 0 \
    -values $ecm -textvariable testing_prefs(gui_brite_topdown_ecm)
  label $wi.topdown.line2.label_k -text "k:"
  # variable zuweisen
  entry $wi.topdown.line2.entry_k -bg white -width 8 -textvariable testing_prefs(gui_brite_topdown_k)
  pack $wi.topdown.line2.entry_k $wi.topdown.line2.label_k $wi.topdown.line2.combo $wi.topdown.line2.label_ecm -side right
  pack $wi.topdown.line2 -side top -anchor w -padx 4 -pady 4

  bind $wi.topdown.line2.combo <<ComboboxSelected>> {
    switched
  }


  frame $wi.topdown.line3
  label $wi.topdown.line3.label_iebwd -text "Inter BW Dist:"
#  set iebwd [linsert $INTEBWDIST 0 "InterBWDist"]
  set iebwd $INTEBWDIST
    ttk::combobox $wi.topdown.line3.combo1 -width 10 -exportselection 0 \
    -values $iebwd -textvariable testing_prefs(gui_brite_topdown_iebwd)
  label $wi.topdown.line3.label_iabwd -text "Intra BW Dist:"
#  set iabwd [linsert $INTABWDIST 0 "IntraBWDist"]
  set iabwd $INTABWDIST
    ttk::combobox $wi.topdown.line3.combo2 -width 10 -exportselection 0 \
    -values $iabwd -textvariable testing_prefs(gui_brite_topdown_iabwd) -state disabled
  pack $wi.topdown.line3.combo2 $wi.topdown.line3.label_iabwd $wi.topdown.line3.combo1 $wi.topdown.line3.label_iebwd -side right
  pack $wi.topdown.line3 -side top -anchor w -padx 4 -pady 4

  frame $wi.topdown.line4
  label $wi.topdown.line4.label_left_maxBW -text "Max BW:"
  entry $wi.topdown.line4.entry_left_maxBW -bg white -width 8 -textvariable testing_prefs(gui_brite_topdown_leftMaxBW)
  label $wi.topdown.line4.label_right_maxBW -text "Max BW:r"
  entry $wi.topdown.line4.entry_right_maxBW -bg white -width 8 -textvariable testing_prefs(gui_brite_topdown_rightMaxBW)
  pack $wi.topdown.line4.entry_right_maxBW $wi.topdown.line4.label_right_maxBW $wi.topdown.line4.entry_left_maxBW $wi.topdown.line4.label_left_maxBW -side right
  pack $wi.topdown.line4 -side top -anchor w -padx 4 -pady 4

  frame $wi.topdown.line5
  label $wi.topdown.line5.label_left_minBW -text "Min BW:"
  entry $wi.topdown.line5.entry_left_minBW -bg white -width 8 -textvariable testing_prefs(gui_brite_topdown_leftMinBW)
  label $wi.topdown.line5.label_right_minBW -text "Min BW:r"
  entry $wi.topdown.line5.entry_right_minBW -bg white -width 8 -textvariable testing_prefs(gui_brite_topdown_rightMinBW)
  pack $wi.topdown.line5.entry_right_minBW $wi.topdown.line5.label_right_minBW $wi.topdown.line5.entry_left_minBW $wi.topdown.line5.label_left_minBW -side right
  pack $wi.topdown.line5 -side top -anchor w -padx 4 -pady 4

  frame $wi.topdown.line6
  #sind die buttons ueberhaupt noch so notwendig.. fkt dahinter implementieren bei bedarf
  # und wieder einkommentieren
  button $wi.topdown.line6.buttonleft -text "Set AS Parameters" -command "setASPara"
  button $wi.topdown.line6.buttonright -text "Set Router Paramters" -command "setRouterPara"
  pack $wi.topdown.line6.buttonright $wi.topdown.line6.buttonleft -side right
  pack $wi.topdown.line6 -side top -anchor w -padx 4 -pady 4

  pack $wi.topdown -side top -fill x

  #
  # Bottom Up (hinten anstellen)
  # hier noch wenn gewuenscht erstellen
  labelframe $wi.bottomup -borderwidth 4 -text "Bottom Up"

  pack $wi.bottomup -side right -fill x


  #
  # Buttons unten
  #

  # TODO huebscher machen
  # aufruf aller vier schritte in einem uebergeordneten schritt
  labelframe $wi.bot5 -borderwidth 4 -text "1st-4th at once"

  frame $wi.bot5.line1 -borderwidth 0

  button $wi.bot5.line1.buildtop -text "GO" -command "doOneToFour"
  pack $wi.bot5.line1.buildtop -side right
  pack $wi.bot5.line1 -side top -anchor w -padx 4 -pady 4
  pack $wi.bot5 -side bottom -fill x

  


  # Script aufruf von .brite in .imn
  labelframe $wi.bot4 -borderwidth 4 -text "4th: Load .imn into GUI"

  frame $wi.bot4.line1 -borderwidth 0

  #label $wi.bot3.line1.text_loadbrite -text "LoadBrite:"
  #entry $wi.bot3.line1.entry_loadbrite -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom3_loadbrite)
  #label $wi.bot3.line1.text_imnout -text "Output:"
  #entry $wi.bot3.line1.entry_imnout -bg white -width 19 -textvariable testing_prefs(gui_brite_bottom3_imnout)

  #$wi.bot3.line1.entry_loadbrite $wi.bot3.line1.text_loadbrite $wi.bot3.line1.entry_imnout $wi.bot3.line1.text_imnout

  button $wi.bot4.line1.buildtop -text "Load .imn" -command "loadIMN"
  pack $wi.bot4.line1.buildtop -side right
  pack $wi.bot4.line1 -side top -anchor w -padx 4 -pady 4
  pack $wi.bot4 -side bottom -fill x



  # Script aufruf von .brite in .imn
  labelframe $wi.bot3 -borderwidth 4 -text "3rd: Build .imn out of .brite"

  frame $wi.bot3.line1 -borderwidth 0

  label $wi.bot3.line1.text_loadbrite -text "LoadBrite:"
  entry $wi.bot3.line1.entry_loadbrite -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom3_loadbrite)
  label $wi.bot3.line1.text_imnout -text "Output:"
  entry $wi.bot3.line1.entry_imnout -bg white -width 19 -textvariable testing_prefs(gui_brite_bottom3_imnout)

  button $wi.bot3.line1.buildtop -text "Build .imn" -command "buildIMN"
  pack $wi.bot3.line1.buildtop $wi.bot3.line1.entry_loadbrite $wi.bot3.line1.text_loadbrite $wi.bot3.line1.entry_imnout $wi.bot3.line1.text_imnout -side right
  pack $wi.bot3.line1 -side top -anchor w -padx 4 -pady 4
  pack $wi.bot3 -side bottom -fill x

  # Topology Erstellungen Einstellungen
  labelframe $wi.bot2 -borderwidth 4 -text "2nd: Build Topology"

  frame $wi.bot2.line1 -borderwidth 0
  label $wi.bot2.line1.text_loadcfg -text "LoadCfg:"
  entry $wi.bot2.line1.entry_loadcfg -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom2_loadcfg)
  label $wi.bot2.line1.text_briteout -text "Output:"
  entry $wi.bot2.line1.entry_briteout -bg white -width 19 -textvariable testing_prefs(gui_brite_bottom2_briteout)
  button $wi.bot2.line1.buildtop -text "Build Topology" -command "buildTopology"
  pack $wi.bot2.line1.buildtop $wi.bot2.line1.entry_loadcfg $wi.bot2.line1.text_loadcfg $wi.bot2.line1.entry_briteout $wi.bot2.line1.text_briteout -side right
  pack $wi.bot2.line1 -side top -anchor w -padx 4 -pady 4
  pack $wi.bot2 -side bottom -fill x


  # Config Einstellungen
  labelframe $wi.bot -borderwidth 4 -text "1st: Config Generation"

  frame $wi.bot.line1 -borderwidth 0
  # unterschied destroy $wi und detroy .core_testing
  #  beides zerstoert das fenster
  button $wi.bot.line1.buildtop -text "Build Cfg" -command "buildCfg"

  label $wi.bot.line1.text_savedest -text "SaveCfg:"
  entry $wi.bot.line1.entry_savedest -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom_savedest)
  label $wi.bot.line1.text_execpath -text "BritePath:"
  entry $wi.bot.line1.entry_execpath -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom_execpath)

  pack $wi.bot.line1.buildtop $wi.bot.line1.entry_savedest $wi.bot.line1.text_savedest $wi.bot.line1.entry_execpath $wi.bot.line1.text_execpath -side right
  pack $wi.bot.line1 -side top -anchor w -padx 4 -pady 4
  pack $wi.bot -side bottom -fill x

  after 100 {
    catch { grab .core_testing }
  }



  # initiale sichtbarkeiten einstellen
  .core_testing.as.line5.entry_p configure -state disabled
  .core_testing.as.line6.entry_q configure -state disabled
  .core_testing.as.line7.entry_gamma configure -state disabled
  .core_testing.as.line8.combo configure -state disabled

  .core_testing.router.line1.import configure -state disabled
  .core_testing.router.line2.entry_hs configure -state disabled
  .core_testing.router.line2.entry_n configure -state disabled
  .core_testing.router.line3.entry_ls configure -state disabled
  .core_testing.router.line3.combo configure -state disabled
  .core_testing.router.line5.combo configure -state disabled
  .core_testing.router.line5.entry_alpha configure -state disabled
  .core_testing.router.line5.entry_p configure -state disabled
  .core_testing.router.line6.entry_q configure -state disabled
  .core_testing.router.line6.combo configure -state disabled
  .core_testing.router.line6.entry_beta configure -state disabled
  .core_testing.router.line7.combo configure -state disabled
  .core_testing.router.line7.entry_gamma configure -state disabled
  .core_testing.router.line8.combo configure -state disabled
  .core_testing.router.line8.entry_m configure -state disabled
  .core_testing.router.line9.combo configure -state disabled
  .core_testing.router.line9.entry_maxBW configure -state disabled
  .core_testing.router.line10.entry_minBW configure -state disabled

  .core_testing.topdown.line2.combo configure -state disabled
  .core_testing.topdown.line2.entry_k configure -state disabled
  .core_testing.topdown.line3.combo1 configure -state disabled
  .core_testing.topdown.line3.combo2 configure -state disabled
  .core_testing.topdown.line4.entry_left_maxBW configure -state disabled
  .core_testing.topdown.line4.entry_right_maxBW configure -state disabled
  .core_testing.topdown.line5.entry_left_minBW configure -state disabled
  .core_testing.topdown.line5.entry_right_minBW configure -state disabled
  .core_testing.topdown.line6.buttonleft configure -state disabled
  .core_testing.topdown.line6.buttonright configure -state disabled


}

# stellt die Topology auf 1 Level: AS ONLY zurueck wenn eine topology generiert wurde
proc zurueck_stellen {} {
  global testing_prefs

  set testing_prefs(gui_brite_top_topotypes) "1 Level: AS ONLY"
  switched
}


proc buildTopology [] {
  global testing_prefs

#testing_prefs(gui_brite_bottom_savedest)
# 373   entry $wi.bot2.entry_execpath -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom2_execpath)
# 375   entry $wi.bot2.entry_loadcfg -bg white -width 17 -textvariable testing_prefs(gui_brite_bottom2_loadcfg)

#  puts [pwd]
#  cd /home/jw/dateien/sw/brite/BRITE/Java
#  puts [pwd]

  set execdir $testing_prefs(gui_brite_bottom_execpath)

  # hier entscheidet sich nach auswahl ob brite mit java oder als exe aufgerufen wird
  if {[string equal "Java" $testing_prefs(gui_brite_top_executables)]} {
    # TODO hier auch schauen
    append execdir "/Java"

    cd $execdir
    puts [pwd]

    set exec_string exec
    lappend exec_string java
    lappend exec_string -Xms2048M -Xmx2048M
    lappend exec_string Main.Brite
    lappend exec_string $testing_prefs(gui_brite_bottom2_loadcfg)
    lappend exec_string $testing_prefs(gui_brite_bottom2_briteout)
    lappend exec_string seed_file
    lappend exec_string >@stdout 2>@stderr &
    {*}$exec_string

  } else {
    # TODO schaun wie das geloest werden soll
    append execdir "/C++"

    cd $execdir
    puts [pwd]

    set exec_string exec
    lappend exec_string ./cppgen
    lappend exec_string $testing_prefs(gui_brite_bottom2_loadcfg)
    lappend exec_string $testing_prefs(gui_brite_bottom2_briteout)
    lappend exec_string seed_file
    lappend exec_string >@stdout 2>@stderr &
    {*}$exec_string
  }

}


proc buildIMN {} {

  global testing_prefs

  # aufruf script von robert mit parametern
  # TODO script execdir anpassen
  set execdir "/home/hanstest"

  cd $execdir
  puts [pwd]


  set exec_string exec
  lappend exec_string ./core_topogen.py
  # pfad zur.brite datei
  lappend exec_string $testing_prefs(gui_brite_bottom3_loadbrite)
  # pfad zur imn ausgabedatei
  lappend exec_string $testing_prefs(gui_brite_bottom3_imnout)

  lappend exec_string "weitere parameter"

  # ist mit und ohne & blockeriend ..
  lappend  exec_string >@stdout 2>@stderr &
  # ausfuehren
  {*}$exec_string

  # gui_brite_bottom3_loadbrite                 "/usr/share/core/topoOut"
  # gui_brite_bottom3_imnout                    "/usr/share/core/topo.imn"
}


proc loadIMN {} {

  global currentFile testing_prefs

  set currentFile $testing_prefs(gui_brite_bottom3_imnout)
  writeBriteConf
  destroy .core_testing
  openFile
  
}


proc doOneToFour {} {

  buildCfg
  buildTopology

  buildIMN
  loadIMN
}

proc switched {} {

  global testing_prefs

  set var [.core_testing.top.line1.combo get]

  if {[string equal "1 Level: AS ONLY" $var]} {

    #.core_testing.as.line1.import configure -state normal
    .core_testing.as.line2.entry_hs configure -state normal
    .core_testing.as.line2.entry_n configure -state normal
    .core_testing.as.line3.entry_ls configure -state normal
    .core_testing.as.line3.combo configure -state normal
    .core_testing.as.line5.combo configure -state normal

    #allgemein je nach auswahl werte anpassen

    set var_as_alpha_beta [.core_testing.as.line3.combo get]
    if {[string equal "Waxman" $var_as_alpha_beta]} {
#      set testing_prefs(gui_brite_as_beta) 0.2

      .core_testing.as.line5.entry_alpha configure -state normal
      .core_testing.as.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_as_alpha_is_disabled) 0
      set testing_prefs(gui_brite_as_beta_is_disabled) 0
      .core_testing.as.line5.entry_p configure -state disabled
      .core_testing.as.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_as_p_is_disabled) 1
      set testing_prefs(gui_brite_as_q_is_disabled) 1

    } elseif {[string equal "BA" $var_as_alpha_beta]} {
      .core_testing.as.line5.entry_alpha configure -state disabled
      .core_testing.as.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_as_alpha_is_disabled) 1
      set testing_prefs(gui_brite_as_beta_is_disabled) 1
      .core_testing.as.line5.entry_p configure -state disabled
      .core_testing.as.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_as_p_is_disabled) 1
      set testing_prefs(gui_brite_as_q_is_disabled) 1

    } elseif {[string equal "BA-2" $var_as_alpha_beta]} {
#      set testing_prefs(gui_brite_as_p) 0.6
#      set testing_prefs(gui_brite_as_q) 0.2

      .core_testing.as.line5.entry_alpha configure -state disabled
      .core_testing.as.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_as_alpha_is_disabled) 1
      set testing_prefs(gui_brite_as_beta_is_disabled) 1
      .core_testing.as.line5.entry_p configure -state normal
      .core_testing.as.line6.entry_q configure -state normal
      set testing_prefs(gui_brite_as_p_is_disabled) 0
      set testing_prefs(gui_brite_as_q_is_disabled) 0

    } else {
#      set testing_prefs(gui_brite_as_p) 0.45
#      set testing_prefs(gui_brite_as_beta) 0.64
#      set testing_prefs(gui_brite_as_m) 1
      .core_testing.as.line5.entry_alpha configure -state disabled
      .core_testing.as.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_as_alpha_is_disabled) 1
      set testing_prefs(gui_brite_as_beta_is_disabled) 0
      .core_testing.as.line5.entry_p configure -state normal
      .core_testing.as.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_as_p_is_disabled) 0
      set testing_prefs(gui_brite_as_q_is_disabled) 1
    }

    .core_testing.as.line6.combo configure -state normal
    .core_testing.as.line7.combo configure -state normal
    .core_testing.as.line7.entry_gamma configure -state disabled
    .core_testing.as.line8.combo configure -state disabled
    .core_testing.router.line1.import configure -state disabled
    .core_testing.router.line2.entry_hs configure -state disabled
    .core_testing.router.line2.entry_n configure -state disabled
    .core_testing.router.line3.entry_ls configure -state disabled
    .core_testing.router.line3.combo configure -state disabled
    .core_testing.router.line5.combo configure -state disabled
    .core_testing.router.line5.entry_alpha configure -state disabled
    .core_testing.router.line5.entry_p configure -state disabled
    .core_testing.router.line6.entry_q configure -state disabled
    .core_testing.router.line6.combo configure -state disabled
    .core_testing.router.line6.entry_beta configure -state disabled
    .core_testing.router.line7.combo configure -state disabled
    .core_testing.router.line7.entry_gamma configure -state disabled
    .core_testing.router.line8.combo configure -state disabled
    .core_testing.router.line8.entry_m configure -state disabled
    .core_testing.router.line9.combo configure -state disabled
    .core_testing.router.line9.entry_maxBW configure -state disabled
    .core_testing.router.line10.entry_minBW configure -state disabled

    .core_testing.topdown.line2.combo configure -state disabled
    .core_testing.topdown.line2.entry_k configure -state disabled
    .core_testing.topdown.line3.combo1 configure -state disabled
    .core_testing.topdown.line3.combo2 configure -state disabled
    .core_testing.topdown.line4.entry_left_maxBW configure -state disabled
    .core_testing.topdown.line4.entry_right_maxBW configure -state disabled
    .core_testing.topdown.line5.entry_left_minBW configure -state disabled
    .core_testing.topdown.line5.entry_right_minBW configure -state disabled
    .core_testing.topdown.line6.buttonleft configure -state disabled
    .core_testing.topdown.line6.buttonright configure -state disabled

    set testing_prefs(gui_brite_top_topotypes_is_disabled) 0
    set testing_prefs(gui_brite_as_models_is_disabled) 0
    set testing_prefs(gui_brite_as_nodeplacement_is_disabled) 0
    set testing_prefs(gui_brite_as_growthtype_is_disabled) 0
    set testing_prefs(gui_brite_as_prefconn_is_disabled) 0
    set testing_prefs(gui_brite_as_connlocali_is_disabled) 1
    set testing_prefs(gui_brite_as_bandwidthd_is_disabled) 0
    set testing_prefs(gui_brite_as_hs_is_disabled) 0
    set testing_prefs(gui_brite_as_n_is_disabled) 0
    set testing_prefs(gui_brite_as_ls_is_disabled) 0
    set testing_prefs(gui_brite_as_gamma_is_disabled) 1
    set testing_prefs(gui_brite_as_m_is_disabled) 0
    set testing_prefs(gui_brite_as_maxBW_is_disabled) 0
    set testing_prefs(gui_brite_as_minBW_is_disabled) 0
    set testing_prefs(gui_brite_router_models_is_disabled) 1
    set testing_prefs(gui_brite_router_nodeplacement_is_disabled) 1
    set testing_prefs(gui_brite_router_growthtype_is_disabled) 1
    set testing_prefs(gui_brite_router_prefconn_is_disabled) 1
    set testing_prefs(gui_brite_router_connlocali_is_disabled) 1
    set testing_prefs(gui_brite_router_bandwidthd_is_disabled) 1
    set testing_prefs(gui_brite_router_hs_is_disabled) 1
    set testing_prefs(gui_brite_router_n_is_disabled) 1
    set testing_prefs(gui_brite_router_ls_is_disabled) 1
    set testing_prefs(gui_brite_router_alpha_is_disabled) 1
    set testing_prefs(gui_brite_router_beta_is_disabled) 1
    set testing_prefs(gui_brite_router_p_is_disabled) 1
    set testing_prefs(gui_brite_router_q_is_disabled) 1
    set testing_prefs(gui_brite_router_gamma_is_disabled) 1
    set testing_prefs(gui_brite_router_m_is_disabled) 1
    set testing_prefs(gui_brite_router_maxBW_is_disabled) 1
    set testing_prefs(gui_brite_router_minBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_k_is_disabled) 1
    set testing_prefs(gui_brite_topdown_rightMaxBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_leftMaxBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_rightMinBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_leftMinBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_ecm_is_disabled) 1
    set testing_prefs(gui_brite_topdown_iebwd_is_disabled) 1
    set testing_prefs(gui_brite_topdown_iabwd_is_disabled) 1


  } elseif {[string equal "1 Level: ROUTER (IP) ONLY" $var]} {

    #.core_testing.as.line1.import configure -state disabled
    .core_testing.as.line2.entry_hs configure -state disabled
    .core_testing.as.line2.entry_n configure -state disabled
    .core_testing.as.line3.entry_ls configure -state disabled
    .core_testing.as.line3.combo configure -state disabled
    .core_testing.as.line5.combo configure -state disabled
    .core_testing.as.line5.entry_alpha configure -state disabled
    .core_testing.as.line5.entry_p configure -state disabled
    .core_testing.as.line6.entry_q configure -state disabled
    .core_testing.as.line6.combo configure -state disabled
    .core_testing.as.line6.entry_beta configure -state disabled
    .core_testing.as.line7.combo configure -state disabled
    .core_testing.as.line7.entry_gamma configure -state disabled
    .core_testing.as.line8.combo configure -state disabled
    .core_testing.as.line8.entry_m configure -state disabled
    .core_testing.as.line9.combo configure -state disabled
    .core_testing.router.line9.entry_maxBW configure -state disabled
    .core_testing.as.line10.entry_minBW configure -state disabled

    .core_testing.router.line1.import configure -state normal
    .core_testing.router.line2.entry_hs configure -state normal
    .core_testing.router.line2.entry_n configure -state normal
    .core_testing.router.line3.entry_ls configure -state normal
    .core_testing.router.line3.combo configure -state normal
    .core_testing.router.line5.combo configure -state normal
    .core_testing.router.line6.combo configure -state normal

    set var_router_alpha_beta [.core_testing.router.line3.combo get]
    if {[string equal "Waxman" $var_router_alpha_beta]} {
      .core_testing.router.line5.entry_alpha configure -state normal
      .core_testing.router.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_router_alpha_is_disabled) 0
      set testing_prefs(gui_brite_router_beta_is_disabled) 0
      .core_testing.router.line5.entry_p configure -state disabled
      .core_testing.router.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_router_p_is_disabled) 1
      set testing_prefs(gui_brite_router_q_is_disabled) 1

    } elseif {[string equal "BA" $var_router_alpha_beta]} {
      .core_testing.router.line5.entry_alpha configure -state disabled
      .core_testing.router.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_router_alpha_is_disabled) 1
      set testing_prefs(gui_brite_router_beta_is_disabled) 1
      .core_testing.router.line5.entry_p configure -state disabled
      .core_testing.router.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_router_p_is_disabled) 1
      set testing_prefs(gui_brite_router_q_is_disabled) 1
    } elseif {[string equal "BA-2" $var_router_alpha_beta]} {
      .core_testing.router.line5.entry_alpha configure -state disabled
      .core_testing.router.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_router_alpha_is_disabled) 1
      set testing_prefs(gui_brite_router_beta_is_disabled) 1
      .core_testing.router.line5.entry_p configure -state normal
      .core_testing.router.line6.entry_q configure -state normal
      set testing_prefs(gui_brite_router_p_is_disabled) 0
      set testing_prefs(gui_brite_router_q_is_disabled) 0
    } else {
      .core_testing.router.line5.entry_alpha configure -state disabled
      .core_testing.router.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_router_alpha_is_disabled) 1
      set testing_prefs(gui_brite_router_beta_is_disabled) 0
      .core_testing.router.line5.entry_p configure -state normal
      .core_testing.router.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_router_p_is_disabled) 0
      set testing_prefs(gui_brite_router_q_is_disabled) 1
    }

    .core_testing.router.line7.combo configure -state normal
    .core_testing.router.line7.entry_gamma configure -state disabled
    .core_testing.router.line8.combo configure -state disabled
    .core_testing.router.line8.entry_m configure -state normal
    .core_testing.router.line9.combo configure -state normal
    .core_testing.router.line9.entry_maxBW configure -state normal
    .core_testing.router.line10.entry_minBW configure -state normal

    .core_testing.topdown.line2.combo configure -state disabled
    .core_testing.topdown.line2.entry_k configure -state disabled
    .core_testing.topdown.line3.combo1 configure -state disabled
    .core_testing.topdown.line3.combo2 configure -state disabled
    .core_testing.topdown.line4.entry_left_maxBW configure -state disabled
    .core_testing.topdown.line4.entry_right_maxBW configure -state disabled
    .core_testing.topdown.line5.entry_left_minBW configure -state disabled
    .core_testing.topdown.line5.entry_right_minBW configure -state disabled
    .core_testing.topdown.line6.buttonleft configure -state disabled
    .core_testing.topdown.line6.buttonright configure -state disabled

    set testing_prefs(gui_brite_top_topotypes_is_disabled) 0
    set testing_prefs(gui_brite_as_models_is_disabled) 1
    set testing_prefs(gui_brite_as_nodeplacement_is_disabled) 1
    set testing_prefs(gui_brite_as_growthtype_is_disabled) 1
    set testing_prefs(gui_brite_as_prefconn_is_disabled) 1
    set testing_prefs(gui_brite_as_connlocali_is_disabled) 1
    set testing_prefs(gui_brite_as_bandwidthd_is_disabled) 1
    set testing_prefs(gui_brite_as_hs_is_disabled) 1
    set testing_prefs(gui_brite_as_n_is_disabled) 1
    set testing_prefs(gui_brite_as_ls_is_disabled) 1
    set testing_prefs(gui_brite_as_alpha_is_disabled) 1
    set testing_prefs(gui_brite_as_beta_is_disabled) 1
    set testing_prefs(gui_brite_as_p_is_disabled) 1
    set testing_prefs(gui_brite_as_q_is_disabled) 1
    set testing_prefs(gui_brite_as_gamma_is_disabled) 1
    set testing_prefs(gui_brite_as_m_is_disabled) 1
    set testing_prefs(gui_brite_as_maxBW_is_disabled) 1
    set testing_prefs(gui_brite_as_minBW_is_disabled) 1
    set testing_prefs(gui_brite_router_models_is_disabled) 0
    set testing_prefs(gui_brite_router_nodeplacement_is_disabled) 0
    set testing_prefs(gui_brite_router_growthtype_is_disabled) 0
    set testing_prefs(gui_brite_router_prefconn_is_disabled) 0
    set testing_prefs(gui_brite_router_connlocali_is_disabled) 0
    set testing_prefs(gui_brite_router_bandwidthd_is_disabled) 0
    set testing_prefs(gui_brite_router_hs_is_disabled) 0
    set testing_prefs(gui_brite_router_n_is_disabled) 0
    set testing_prefs(gui_brite_router_ls_is_disabled) 0
    set testing_prefs(gui_brite_router_gamma_is_disabled) 0
    set testing_prefs(gui_brite_router_m_is_disabled) 0
    set testing_prefs(gui_brite_router_maxBW_is_disabled) 0
    set testing_prefs(gui_brite_router_minBW_is_disabled) 0
    set testing_prefs(gui_brite_topdown_k_is_disabled) 1
    set testing_prefs(gui_brite_topdown_rightMaxBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_leftMaxBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_rightMinBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_leftMinBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_ecm_is_disabled) 1
    set testing_prefs(gui_brite_topdown_iebwd_is_disabled) 1
    set testing_prefs(gui_brite_topdown_iabwd_is_disabled) 1


  } elseif {[string equal "2 Level: TOP-DOWN" $var]} {

    #.core_testing.as.line1.import configure -state normal
    .core_testing.as.line2.entry_hs configure -state normal
    .core_testing.as.line2.entry_n configure -state normal
    .core_testing.as.line3.entry_ls configure -state normal
    .core_testing.as.line3.combo configure -state normal
    .core_testing.as.line5.combo configure -state normal

    set var_as_alpha_beta [.core_testing.as.line3.combo get]
    if {[string equal "Waxman" $var_as_alpha_beta]} {
      .core_testing.as.line5.entry_alpha configure -state normal
      .core_testing.as.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_as_alpha_is_disabled) 0
      set testing_prefs(gui_brite_as_beta_is_disabled) 0
      .core_testing.as.line5.entry_p configure -state disabled
      .core_testing.as.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_as_p_is_disabled) 1
      set testing_prefs(gui_brite_as_q_is_disabled) 1

    } elseif {[string equal "BA" $var_as_alpha_beta]} {
      .core_testing.as.line5.entry_alpha configure -state disabled
      .core_testing.as.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_as_alpha_is_disabled) 1
      set testing_prefs(gui_brite_as_beta_is_disabled) 1
      .core_testing.as.line5.entry_p configure -state disabled
      .core_testing.as.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_as_p_is_disabled) 1
      set testing_prefs(gui_brite_as_q_is_disabled) 1

    } elseif {[string equal "BA-2" $var_as_alpha_beta]} {
      .core_testing.as.line5.entry_alpha configure -state disabled
      .core_testing.as.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_as_alpha_is_disabled) 1
      set testing_prefs(gui_brite_as_beta_is_disabled) 1
      .core_testing.as.line5.entry_p configure -state normal
      .core_testing.as.line6.entry_q configure -state normal
      set testing_prefs(gui_brite_as_p_is_disabled) 0
      set testing_prefs(gui_brite_as_q_is_disabled) 0

    } else {
      .core_testing.as.line5.entry_alpha configure -state disabled
      .core_testing.as.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_as_alpha_is_disabled) 1
      set testing_prefs(gui_brite_as_beta_is_disabled) 0
      .core_testing.as.line5.entry_p configure -state normal
      .core_testing.as.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_as_p_is_disabled) 0
      set testing_prefs(gui_brite_as_q_is_disabled) 1
    }

    .core_testing.as.line6.combo configure -state normal
    .core_testing.as.line7.combo configure -state normal
    .core_testing.as.line7.entry_gamma configure -state disabled
    .core_testing.as.line8.combo configure -state disabled
    .core_testing.as.line8.entry_m configure -state normal
    .core_testing.as.line9.combo configure -state disabled
    .core_testing.as.line9.entry_maxBW configure -state disabled
    .core_testing.as.line10.entry_minBW configure -state disabled

    .core_testing.router.line1.import configure -state normal
    .core_testing.router.line2.entry_hs configure -state normal
    .core_testing.router.line2.entry_n configure -state normal
    .core_testing.router.line3.entry_ls configure -state normal
    .core_testing.router.line3.combo configure -state normal
    .core_testing.router.line5.combo configure -state normal

    set var_router_alpha_beta [.core_testing.router.line3.combo get]
    if {[string equal "Waxman" $var_router_alpha_beta]} {
      .core_testing.router.line5.entry_alpha configure -state normal
      .core_testing.router.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_router_alpha_is_disabled) 0
      set testing_prefs(gui_brite_router_beta_is_disabled) 0
      .core_testing.router.line5.entry_p configure -state disabled
      .core_testing.router.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_router_p_is_disabled) 1
      set testing_prefs(gui_brite_router_q_is_disabled) 1

    } elseif {[string equal "BA" $var_router_alpha_beta]} {
      .core_testing.router.line5.entry_alpha configure -state disabled
      .core_testing.router.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_router_alpha_is_disabled) 1
      set testing_prefs(gui_brite_router_beta_is_disabled) 1
      .core_testing.router.line5.entry_p configure -state disabled
      .core_testing.router.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_router_p_is_disabled) 1
      set testing_prefs(gui_brite_router_q_is_disabled) 1
    } elseif {[string equal "BA-2" $var_router_alpha_beta]} {
      .core_testing.router.line5.entry_alpha configure -state disabled
      .core_testing.router.line6.entry_beta configure -state disabled
      set testing_prefs(gui_brite_router_alpha_is_disabled) 1
      set testing_prefs(gui_brite_router_beta_is_disabled) 1
      .core_testing.router.line5.entry_p configure -state normal
      .core_testing.router.line6.entry_q configure -state normal
      set testing_prefs(gui_brite_router_p_is_disabled) 0
      set testing_prefs(gui_brite_router_q_is_disabled) 0
    } else {
      .core_testing.router.line5.entry_alpha configure -state disabled
      .core_testing.router.line6.entry_beta configure -state normal
      set testing_prefs(gui_brite_router_alpha_is_disabled) 1
      set testing_prefs(gui_brite_router_beta_is_disabled) 0
      .core_testing.router.line5.entry_p configure -state normal
      .core_testing.router.line6.entry_q configure -state disabled
      set testing_prefs(gui_brite_router_p_is_disabled) 0
      set testing_prefs(gui_brite_router_q_is_disabled) 1
    }


    .core_testing.router.line6.combo configure -state normal
    .core_testing.router.line7.combo configure -state normal
    .core_testing.router.line7.entry_gamma configure -state disabled
    .core_testing.router.line8.combo configure -state disabled
    .core_testing.router.line8.entry_m configure -state normal
    .core_testing.router.line9.combo configure -state disabled
    .core_testing.router.line9.entry_maxBW configure -state disabled
    .core_testing.router.line10.entry_minBW configure -state disabled

    .core_testing.topdown.line2.combo configure -state normal

    set var_topdown_k [.core_testing.topdown.line2.combo get]
    if {[string equal "Smallest k-Degree" $var_topdown_k]} {
      .core_testing.topdown.line2.entry_k configure -state normal
      set testing_prefs(gui_brite_topdown_k_is_disabled) 0
    } else {
      .core_testing.topdown.line2.entry_k configure -state disabled
      set testing_prefs(gui_brite_topdown_k_is_disabled) 1
    }

    .core_testing.topdown.line3.combo1 configure -state normal
    .core_testing.topdown.line3.combo2 configure -state normal
    .core_testing.topdown.line4.entry_left_maxBW configure -state normal
    .core_testing.topdown.line4.entry_right_maxBW configure -state normal
    .core_testing.topdown.line5.entry_left_minBW configure -state normal
    .core_testing.topdown.line5.entry_right_minBW configure -state normal
    .core_testing.topdown.line6.buttonleft configure -state normal
    .core_testing.topdown.line6.buttonright configure -state normal


    set testing_prefs(gui_brite_top_topotypes_is_disabled) 0
    set testing_prefs(gui_brite_as_models_is_disabled) 0
    set testing_prefs(gui_brite_as_nodeplacement_is_disabled) 0
    set testing_prefs(gui_brite_as_growthtype_is_disabled) 0
    set testing_prefs(gui_brite_as_prefconn_is_disabled) 0
    set testing_prefs(gui_brite_as_connlocali_is_disabled) 1
    set testing_prefs(gui_brite_as_bandwidthd_is_disabled) 1
    set testing_prefs(gui_brite_as_hs_is_disabled) 0
    set testing_prefs(gui_brite_as_n_is_disabled) 0
    set testing_prefs(gui_brite_as_ls_is_disabled) 0
    set testing_prefs(gui_brite_as_gamma_is_disabled) 1
    set testing_prefs(gui_brite_as_m_is_disabled) 0
    set testing_prefs(gui_brite_as_maxBW_is_disabled) 1
    set testing_prefs(gui_brite_as_minBW_is_disabled) 1
    set testing_prefs(gui_brite_router_models_is_disabled) 0
    set testing_prefs(gui_brite_router_nodeplacement_is_disabled) 0
    set testing_prefs(gui_brite_router_growthtype_is_disabled) 0
    set testing_prefs(gui_brite_router_prefconn_is_disabled) 0
    set testing_prefs(gui_brite_router_connlocali_is_disabled) 1
    set testing_prefs(gui_brite_router_bandwidthd_is_disabled) 1
    set testing_prefs(gui_brite_router_hs_is_disabled) 0
    set testing_prefs(gui_brite_router_n_is_disabled) 0
    set testing_prefs(gui_brite_router_ls_is_disabled) 0
    set testing_prefs(gui_brite_router_gamma_is_disabled) 1
    set testing_prefs(gui_brite_router_m_is_disabled) 0
    set testing_prefs(gui_brite_router_maxBW_is_disabled) 1
    set testing_prefs(gui_brite_router_minBW_is_disabled) 1
    set testing_prefs(gui_brite_topdown_rightMaxBW_is_disabled) 0
    set testing_prefs(gui_brite_topdown_leftMaxBW_is_disabled) 0
    set testing_prefs(gui_brite_topdown_rightMinBW_is_disabled) 0
    set testing_prefs(gui_brite_topdown_leftMinBW_is_disabled) 0
    set testing_prefs(gui_brite_topdown_ecm_is_disabled) 0
    set testing_prefs(gui_brite_topdown_iebwd_is_disabled) 0
    set testing_prefs(gui_brite_topdown_iabwd_is_disabled) 0


  } elseif {[string equal "2 Level: BOTTOM-UP" $var]} {

#    .core_testing.as.line1.import configure -state
#    .core_testing.as.line2.entry_hs configure -state
#    .core_testing.as.line2.entry_n configure -state
#    .core_testing.as.line3.entry_ls configure -state
#    .core_testing.as.line3.combo configure -state
#    .core_testing.as.line5.combo configure -state
#    .core_testing.as.line5.entry_alpha configure -state
#    .core_testing.as.line6.combo configure -state
#    .core_testing.as.line6.entry_beta configure -state
#    .core_testing.as.line7.combo configure -state
#    .core_testing.as.line7.entry_gamma configure -state
#    .core_testing.as.line8.combo configure -state
#    .core_testing.as.line8.entry_m configure -state
#    .core_testing.as.line9.combo configure -state
#    .core_testing.router.line9.entry_maxBW configure -state
#    .core_testing.as.line10.entry_minBW configure -state
#
#    .core_testing.router.line1.import configure -state
#    .core_testing.router.line2.entry_hs configure -state
#    .core_testing.router.line2.entry_n configure -state
#    .core_testing.router.line3.entry_ls configure -state
#    .core_testing.router.line3.combo configure -state
#    .core_testing.router.line5.combo configure -state
#    .core_testing.router.line5.entry_alpha configure -state
#    .core_testing.router.line6.combo configure -state
#    .core_testing.router.line6.entry_beta configure -state
#    .core_testing.router.line7.combo configure -state
#    .core_testing.router.line7.entry_gamma configure -state
#    .core_testing.router.line8.combo configure -state
#    .core_testing.router.line8.entry_m configure -state
#    .core_testing.router.line9.combo configure -state
#    .core_testing.router.line9.entry_maxBW configure -state
#    .core_testing.router.line10.entry_minBW configure -state
#
#    .core_testing.topdown.line2.combo configure -state
#    .core_testing.topdown.line2.entry_k configure -state
#    .core_testing.topdown.line3.combo1 configure -state
#    .core_testing.topdown.line3.combo2 configure -state
#    .core_testing.topdown.line4.entry_left_maxBW configure -state
#    .core_testing.topdown.line4.entry_right_maxBW configure -state
#    .core_testing.topdown.line5.entry_left_minBW configure -state
#    .core_testing.topdown.line5.entry_right_minBW configure -state
#    .core_testing.topdown.line6.buttonleft configure -state
#    .core_testing.topdown.line6.buttonright configure -state
#
#    set testing_prefs(gui_brite_top_topotypes_is_disabled) 0
#    set testing_prefs(gui_brite_as_models_is_disabled) 0
#    set testing_prefs(gui_brite_as_nodeplacement_is_disabled) 0
#    set testing_prefs(gui_brite_as_growthtype_is_disabled) 0
#    set testing_prefs(gui_brite_as_prefconn_is_disabled) 0
#    set testing_prefs(gui_brite_as_connlocali_is_disabled) 0
#    set testing_prefs(gui_brite_as_bandwidthd_is_disabled) 0
#    set testing_prefs(gui_brite_as_hs_is_disabled) 0
#    set testing_prefs(gui_brite_as_n_is_disabled) 0
#    set testing_prefs(gui_brite_as_ls_is_disabled) 0
#    set testing_prefs(gui_brite_as_alpha_is_disabled) 0
#    set testing_prefs(gui_brite_as_beta_is_disabled) 0
#    set testing_prefs(gui_brite_as_gamma_is_disabled) 0
#    set testing_prefs(gui_brite_as_m_is_disabled) 0
#    set testing_prefs(gui_brite_as_maxBW_is_disabled) 0
#    set testing_prefs(gui_brite_as_minBW_is_disabled) 0
#    set testing_prefs(gui_brite_router_models_is_disabled) 0
#    set testing_prefs(gui_brite_router_nodeplacement_is_disabled) 0
#    set testing_prefs(gui_brite_router_growthtype_is_disabled) 0
#    set testing_prefs(gui_brite_router_prefconn_is_disabled) 0
#    set testing_prefs(gui_brite_router_connlocali_is_disabled) 0
#    set testing_prefs(gui_brite_router_bandwidthd_is_disabled) 0
#    set testing_prefs(gui_brite_router_hs_is_disabled) 0
#    set testing_prefs(gui_brite_router_n_is_disabled) 0
#    set testing_prefs(gui_brite_router_ls_is_disabled) 0
#    set testing_prefs(gui_brite_router_alpha_is_disabled) 0
#    set testing_prefs(gui_brite_router_beta_is_disabled) 0
#    set testing_prefs(gui_brite_router_gamma_is_disabled) 0
#    set testing_prefs(gui_brite_router_m_is_disabled) 0
#    set testing_prefs(gui_brite_router_maxBW_is_disabled) 0
#    set testing_prefs(gui_brite_router_minBW_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_k_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_rightMaxBW_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_leftMaxBW_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_rightMinBW_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_leftMinBW_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_ecm_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_iebwd_is_disabled) 0
#    set testing_prefs(gui_brite_topdown_iabwd_is_disabled) 0


  } else {

    puts "instructions not clear, .."
  }
}



# schreibt config daten in datei
# bisher sehr rudimentaer ohne große intelligenz
proc buildCfg {} {

  global testing_prefs

#  wie im bsp saveDotfile als speicherdialog BZW anderen mit entry feld.

# BSP WERTE ZUWEISUNGEN
# Name = 1 - 5 | 1:Waxman, 2:Barabasi/Waxman, 3:AS Waxman, 4:AS Barabasi,5:Top Down
# edgeConn = 1 - 4 | 1:Random, 2:Smallest Nonleaf, 3:Smallest Deg, 4:k-Degree
# k = -1 - x | if not set -1
# BWInter = 1 - 4 | 1:Constant, 2:Uniform, 3:HeavyTailed, 4: Exponential
# BWInterMin = x | Standard 10
# BWInterMax = x | Standard 1024
# BWIntra = 1 - 4 | 1:Constant, 2:Uniform, 3:HeavyTailed, 4: Exponential
# BWIntraMin = x | Standard 10
# BWIntraMax = x | Standard 1024
#
# N = x | Nodes in Graph Standard 10000
# HS = x | main plane  (number of squares) Standard 1000
# LS = x | inner planes (number of squares) Standard 100
# NodePlacement = 1 - 2 | 1:Random, 2:HeavyTailed
# GrowthType = 1 - 2 | 1:Incremental, 2:All
# m = x | "number of neighbouring node each node connects to"
# alpha = x.x | waxman parameter
# beta = x.x | waxman parameter
# gamma = x.x |
# BWDist = 1 - 4 | 1:Constant, 2:Uniform, 3:HeavyTailed, 4:Exponential
# BWMin = x | Standard -1 Unlimited
# BWMax = x | Standard -1 Unlimited
#
# Output Standard Used:
# BRITE = 1 | output in BRITE Format


  # Beginn immer das Selbe
  set data "# this config file was generated by buildTopology Fkt in /usr/lib/core/brite.tcl\n\n"
  append data "BriteConfig\n"
  append data "\n"

 set var_model [.core_testing.top.line1.combo get]

 if {[string equal "1 Level: AS ONLY" $var_model]} {
# Abschnitt AS ONLY
    append data "BeginModel\n"
    set var_as_alpha_beta [.core_testing.as.line3.combo get]
    if {[string equal "Waxman" $var_as_alpha_beta]} {
      append data "	 Name = 3\n"
    } elseif {[string equal "BA" $var_as_alpha_beta]} {
      append data "	 Name = 4\n"
    } elseif {[string equal "BA-2" $var_as_alpha_beta]} {
      append data "      Name = 10\n"
    } else {
      append data "      Name = 12\n"
      # fall GLP
      #append data "      Name = 4\n"
    }

    # ueberlegen ob besser wenn entry felder ausgelesen oder testing_prefs variable
    append data "	 N = " $testing_prefs(gui_brite_as_n)\n
    append data "	 HS = " $testing_prefs(gui_brite_as_hs)\n
    append data "	 LS = " $testing_prefs(gui_brite_as_ls)\n

    set var_as_node_placement [.core_testing.as.line5.combo get]
    if {[string equal "Random" $var_as_node_placement]} {
      append data "	 NodePlacement = 1\n"
    } else {
      append data "	 NodePlacement = 2\n"
    }

    if {[string equal "Waxman" $var_as_alpha_beta]} {
      set var_as_growth_type [.core_testing.as.line6.combo get]
      if {[string equal "Incremental" $var_as_growth_type]} {
        append data "	 GrowthType = 1\n"
      } else {
        append data "	 GrowthType = 2\n"
      }
    } else {
      #append data "      Name = 4\n"
    }

    # Pref. Conn: wird nicht weiter beachtet?

    append data "	 m = " $testing_prefs(gui_brite_as_m)\n

    if {[string equal "Waxman" $var_as_alpha_beta]} {
      append data "	 alpha = " $testing_prefs(gui_brite_as_alpha)\n
      append data "	 beta = " $testing_prefs(gui_brite_as_beta)\n
    } else {
      #append data "      Name = 4\n"
    }

    # Im Brite Original sind bei bandwidth distribution Punkt 4 und 3 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_as_bandwdistr [.core_testing.as.line9.combo get]
    if {[string equal "Constant" $var_as_bandwdistr]} {
      append data "	 BWDist = 1\n"
    } elseif {[string equal "Uniform" $var_as_bandwdistr]} {
      append data "	 BWDist = 2\n"
    } elseif {[string equal "Exponential" $var_as_bandwdistr]} {
      append data "	 BWDist = 3\n"
    } else {
      append data "	 BWDist = 4\n"
    }
    append data "	 BWMin = " $testing_prefs(gui_brite_as_minBW)\n
    append data "	 BWMax = " $testing_prefs(gui_brite_as_maxBW)\n

    if {[string equal "BA-2" $var_as_alpha_beta]} {
      append data "	  q = " $testing_prefs(gui_brite_as_p)\n
      append data "	  p = " $testing_prefs(gui_brite_as_q)\n
    } elseif {[string equal "GLP" $var_as_alpha_beta]} {
      append data "	  p = " $testing_prefs(gui_brite_as_p)\n
      append data "	  beta = " $testing_prefs(gui_brite_as_beta)\n
    } else {
      # leer
    }

    append data "EndModel\n"
    append data "\n"


  } elseif {[string equal "1 Level: ROUTER (IP) ONLY" $var_model]} {
# Abschnitt Router ONLY
    append data "BeginModel\n"
    set var_router_alpha_beta [.core_testing.router.line3.combo get]
    if {[string equal "Waxman" $var_router_alpha_beta]} {
      append data "	 Name = 1\n"
    } elseif {[string equal "BA" $var_router_alpha_beta]} {
      append data "      Name = 2\n"
    } elseif {[string equal "BA-2" $var_router_alpha_beta]} {
      append data "      Name = 9\n"
    } else {
      # fall GLP
      append data "      Name = 11\n"
      #append data "      Name = 4\n"
    }



    # ueberlegen ob besser wenn entry felder ausgelesen oder testing_prefs variable
    #    append data "	" N = ".core_testing.as.line2.entry_n\n"
    append data "	 N = " $testing_prefs(gui_brite_router_n)\n
    append data "	 HS = " $testing_prefs(gui_brite_router_hs)\n
    append data "	 LS = " $testing_prefs(gui_brite_router_ls)\n

    set var_router_node_placement [.core_testing.router.line5.combo get]
    if {[string equal "Random" $var_router_node_placement]} {
      append data "	 NodePlacement = 1\n"
    } else {
      append data "	 NodePlacement = 2\n"
    }

    if {[string equal "Waxman" $var_router_alpha_beta]} {
      set var_router_growth_type [.core_testing.router.line6.combo get]
      if {[string equal "Incremental" $var_router_growth_type]} {
        append data "	 GrowthType = 1\n"
      } else {
        append data "	 GrowthType = 2\n"
      }
    } else {
      #append data "      Name = 4\n"
    }

    # Pref. Conn: wird nicht weiter beachtet?

    append data "	 m = " $testing_prefs(gui_brite_router_m)\n

    if {[string equal "Waxman" $var_router_alpha_beta]} {
      append data "	 alpha = " $testing_prefs(gui_brite_router_alpha)\n
      append data "	 beta = " $testing_prefs(gui_brite_router_beta)\n
    } else {
      #append data "      Name = 4\n"
    }

    # Im Brite Original sind bei bandwidth distribution Punkt 4 und 3 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_router_bandwdistr [.core_testing.router.line9.combo get]
    if {[string equal "Constant" $var_router_bandwdistr]} {
      append data "	 BWDist = 1\n"
    } elseif {[string equal "Uniform" $var_router_bandwdistr]} {
      append data "	 BWDist = 2\n"
    } elseif {[string equal "Exponential" $var_router_bandwdistr]} {
      append data "	 BWDist = 3\n"
    } else {
      append data "	 BWDist = 4\n"
    }
    append data "	 BWMin = " $testing_prefs(gui_brite_router_minBW)\n
    append data "	 BWMax = " $testing_prefs(gui_brite_router_maxBW)\n

    if {[string equal "BA-2" $var_router_alpha_beta]} {
      append data "       q = " $testing_prefs(gui_brite_router_p)\n
      append data "       p = " $testing_prefs(gui_brite_router_q)\n
    } elseif {[string equal "GLP" $var_router_alpha_beta]} {
      append data "       p = " $testing_prefs(gui_brite_router_p)\n
      append data "       beta = " $testing_prefs(gui_brite_router_beta)\n
    } else {
      # leer
    }

    append data "EndModel\n"
    append data "\n"

  } elseif {[string equal "2 Level: TOP-DOWN" $var_model]} {
# Abschnitt TopDown
# TODO: spaeter vielleicht um doppelten code zu vermeiden
#   teile in fktn auslagern

    append data "BeginModel\n"
    append data "	Name = 5\n"

    # Im Brite Original sind Option 2 und 3 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_topdown_ecm [.core_testing.topdown.line2.combo get]
    if {[string equal "Random" $var_topdown_ecm]} {
      append data "	edgeConn = 1\n"
      append data "	k = -1\n"
    } elseif {[string equal "Smallest-Degree" $var_topdown_ecm]} {
      append data "	edgeConn = 2\n"
      append data "	k = -1\n"
    } elseif {[string equal "Smallest-Degree NonLeaf" $var_topdown_ecm]} {
      append data "	edgeConn = 3\n"
      append data "	k = -1\n"
    } else {
#      append data "_"
#      append $var_topdown_ecm
#      append "_\n"
      append data "	edgeConn = 4\n"
      append data "	k = " $testing_prefs(gui_brite_topdown_k)\n
    }

    # Im Brite Original sind Option 3 und 4 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_topdown_inter_bw [.core_testing.topdown.line3.combo1 get]
    if {[string equal "Constant" $var_topdown_inter_bw]} {
      append data "	BWInter = 1\n"
    } elseif {[string equal "Uniform" $var_topdown_inter_bw]} {
      append data "	BWInter = 2\n"
    } elseif {[string equal "Heavy Tailed" $var_topdown_inter_bw]} {
      append data "	BWInter = 3\n"
    } else {
      append data "	BWInter = 4\n"
    }
    append data "	BWInterMin = " $testing_prefs(gui_brite_topdown_leftMinBW)\n
    append data "	BWInterMax = " $testing_prefs(gui_brite_topdown_leftMaxBW)\n

    # Im Brite Original sind Option 3 und 4 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_topdown_intra_bw [.core_testing.topdown.line3.combo2 get]
    if {[string equal "Constant" $var_topdown_intra_bw]} {
      append data "	BWIntra = 1\n"
    } elseif {[string equal "Uniform" $var_topdown_intra_bw]} {
      append data "	BWIntra = 2\n"
    } elseif {[string equal "Heavy Tailed" $var_topdown_intra_bw]} {
      append data "	BWIntra = 3\n"
    } else {
      append data "	BWIntra = 4\n"
    }
    append data "	BWIntraMin = " $testing_prefs(gui_brite_topdown_rightMinBW)\n
    append data "	BWIntraMax = " $testing_prefs(gui_brite_topdown_rightMaxBW)\n

    append data "EndModel\n"
    append data "\n"


    # AS Anteil
    append data "BeginModel\n"
    set var_as_alpha_beta [.core_testing.as.line3.combo get]
    if {[string equal "Waxman" $var_as_alpha_beta]} {
      append data "	 Name = 3\n"
    } elseif {[string equal "BA" $var_as_alpha_beta]} {
      append data "	 Name = 4\n"
    } elseif {[string equal "BA-2" $var_as_alpha_beta]} {
      append data "	 Name = 10\n"
    } else {
      # fall GLP
      append data "	 Name = 12\n"
      #append data "      Name = 4\n"
    }


    # ueberlegen ob besser wenn entry felder ausgelesen oder testing_prefs variable
    #    append data "	" N = ".core_testing.as.line2.entry_n\n"
    append data "	 N = " $testing_prefs(gui_brite_as_n)\n
    append data "	 HS = " $testing_prefs(gui_brite_as_hs)\n
    append data "	 LS = " $testing_prefs(gui_brite_as_ls)\n

    set var_as_node_placement [.core_testing.as.line5.combo get]
    if {[string equal "Random" $var_as_node_placement]} {
      append data "	 NodePlacement = 1\n"
    } else {
      append data "	 NodePlacement = 2\n"
    }



    if {[string equal "Waxman" $var_as_alpha_beta]} {
      set var_as_growth_type [.core_testing.as.line6.combo get]
      if {[string equal "Incremental" $var_as_growth_type]} {
        append data "	 GrowthType = 1\n"
      } else {
        append data "	 GrowthType = 2\n"
      }
    } else {
      #append data "      Name = 4\n"
    }

    # Pref. Conn: wird nicht weiter beachtet?

    append data "	 m = " $testing_prefs(gui_brite_as_m)\n

    if {[string equal "Waxman" $var_as_alpha_beta]} {
      append data "	 alpha = " $testing_prefs(gui_brite_as_alpha)\n
      append data "	 beta = " $testing_prefs(gui_brite_as_beta)\n
    } else {
      #append data "      Name = 4\n"
    }


    # Im Brite Original sind bandwidth distribution 3 und 4 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_topdown_bandwdistr_as [.core_testing.topdown.line3.combo1 get]
    if {[string equal "Constant" $var_topdown_bandwdistr_as]} {
      append data "	 BWDist = 1\n"
    } elseif {[string equal "Uniform" $var_topdown_bandwdistr_as]} {
      append data "	 BWDist = 2\n"
    } elseif {[string equal "Exponential" $var_topdown_bandwdistr_as]} {
      append data "	 BWDist = 4\n"
    } else {
      append data "	 BWDist = 3\n"
    }
#    append data "	 BWMin = " $testing_prefs(gui_brite_as_minBW)\n
#    append data "	 BWMax = " $testing_prefs(gui_brite_as_maxBW)\n
    append data "	 BWMin = " $testing_prefs(gui_brite_topdown_leftMinBW)\n
    append data "	 BWMax = " $testing_prefs(gui_brite_topdown_leftMaxBW)\n

    if {[string equal "BA-2" $var_as_alpha_beta]} {
      append data "	  q = " $testing_prefs(gui_brite_as_p)\n
      append data "	  p = " $testing_prefs(gui_brite_as_q)\n
    } elseif {[string equal "GLP" $var_as_alpha_beta]} {
      append data "	  p = " $testing_prefs(gui_brite_as_p)\n
      append data "	  beta = " $testing_prefs(gui_brite_as_beta)\n
    } else {
      # leer
    }

    append data "EndModel\n"
    append data "\n"



    # Router Anteil
    append data "BeginModel\n"
    set var_router_alpha_beta [.core_testing.router.line3.combo get]
    if {[string equal "Waxman" $var_router_alpha_beta]} {
      append data "	 Name = 1\n"
    } elseif {[string equal "BA" $var_router_alpha_beta]} {
      append data "	 Name = 2\n"
    } elseif {[string equal "BA-2" $var_router_alpha_beta]} {
      append data "	 Name = 9\n"
    } else {
      # fall GLP
      append data "	 Name = 11\n"
      #append data "      Name = 4\n"
    }


    # ueberlegen ob besser wenn entry felder ausgelesen oder testing_prefs variable
    #    append data "	" N = ".core_testing.as.line2.entry_n\n"
    append data "	 N = " $testing_prefs(gui_brite_router_n)\n
    append data "	 HS = " $testing_prefs(gui_brite_router_hs)\n
    append data "	 LS = " $testing_prefs(gui_brite_router_ls)\n

    set var_router_node_placement [.core_testing.router.line5.combo get]
    if {[string equal "Random" $var_router_node_placement]} {
      append data "	 NodePlacement = 1\n"
    } else {
      append data "	 NodePlacement = 2\n"
    }

    if {[string equal "Waxman" $var_router_alpha_beta]} {
      set var_router_growth_type [.core_testing.router.line6.combo get]
      if {[string equal "Incremental" $var_router_growth_type]} {
        append data "	 GrowthType = 1\n"
      } else {
        append data "	 GrowthType = 2\n"
      }
    } else {
      #append data "      Name = 4\n"
    }

    # Pref. Conn: wird nicht weiter beachtet?

    append data "	 m = " $testing_prefs(gui_brite_router_m)\n

    if {[string equal "Waxman" $var_router_alpha_beta]} {
      append data "	 alpha = " $testing_prefs(gui_brite_router_alpha)\n
      append data "	 beta = " $testing_prefs(gui_brite_router_beta)\n
    } else {
      #append data "      Name = 4\n"
    }

    # Im Brite Original sind bandwidth distribution 3 und 4 vertauscht.
    #   Scheint letzen endes dann doch zu passen bzw hier kommt das selbe falsche/richtige
    #   Ergebnis wie im original Brite.
    set var_topdown_bandwdistr_router [.core_testing.topdown.line3.combo2 get]
    if {[string equal "Constant" $var_topdown_bandwdistr_router]} {
      append data "	 BWDist = 1\n"
    } elseif {[string equal "Uniform" $var_topdown_bandwdistr_router]} {
      append data "	 BWDist = 2\n"
    } elseif {[string equal "Exponential" $var_topdown_bandwdistr_router]} {
      append data "	 BWDist = 4\n"
    } else {
      append data "	 BWDist = 3\n"
    }
#    append data "	 BWMin = " $testing_prefs(gui_brite_router_minBW)\n
#    append data "	 BWMax = " $testing_prefs(gui_brite_router_maxBW)\n
    append data "	 BWMin = " $testing_prefs(gui_brite_topdown_rightMinBW)\n
    append data "	 BWMax = " $testing_prefs(gui_brite_topdown_rightMaxBW)\n

    if {[string equal "BA-2" $var_router_alpha_beta]} {
      append data "	  q = " $testing_prefs(gui_brite_router_p)\n
      append data "	  p = " $testing_prefs(gui_brite_router_q)\n
    } elseif {[string equal "GLP" $var_router_alpha_beta]} {
      append data "	  p = " $testing_prefs(gui_brite_router_p)\n
      append data "	  beta = " $testing_prefs(gui_brite_router_beta)\n
    } else {
      # leer
    }

    append data "EndModel\n"
    append data "\n"

  } elseif {[string equal "2 Level: BOTTOM-UP" $var_model]} {
    # gibts noch nicht
  } else {
    # wird es niemals geben.. fehler
  }


  append data "BeginOutput\n"
  append data "	BRITE = 1\n"
  append data "	OTTER = 0\n"
  append data "	DML = 0\n"
  append data "	NS = 0\n"
  append data "	Javasim = 0\n"
  append data "EndOutput"

#  Auschnitt aus dem Original Configfile
#        BRITE = 1        #1/0=enable/disable output in BRITE format
#        OTTER = 0        #1/0=enable/disable visualization in otter
#        DML = 0          #1/0=enable/disable output to SSFNet's DML format
#        NS = 0   #1/0=enable/disable output to NS-2
#        Javasim = 0      #1/0=enable/disable output to Javasim
#




  set filename $testing_prefs(gui_brite_bottom_savedest)
#  set filename "/home/jw/Desktop/test.txt"
  set fileId [open $filename "w"]
  puts $fileId $data
  close $fileId
}


proc writeBriteConf { } {

  global CONFDIR testing_prefs

   set briteconfname "$CONFDIR/brite.conf"
    if { [catch { set britef [open "$briteconfname" w] } ] } {
        puts "***Warning: could not write brite file: $briteconfname"
        return
    }

  set briteheader "# brite.conf for brite configuration stuff"
  puts $britef $briteheader

  puts $britef "array set testing_prefs {"


  # gib alle elemente in testing_prefs / sortiere dict style
  foreach pref [lsort -dict [array names testing_prefs]] {
    set value $testing_prefs($pref)
    set tabs "\t\t"
    if { [string length $pref] >= 16 } { set tabs "\t" }
    puts $britef "\t$pref$tabs\"$value\""
  }
  puts $britef "}"
  close $britef

}


proc loadBriteConf { } {

  global CONFDIR testing_prefs

  if {[catch {set britef [open "$CONFDIR/brite.conf" r]} ]} return
  close $britef


  #fuehrt die conf datei als quasi script aus und liest die variablen ein
  if {[catch { source "$CONFDIR/brite.conf" }]} {
      puts "The $CONFDIR/brite.conf preferences file is invalid, ignoring it."
      return
  }

}

# variablen definition fuer Testing GUI nach
# Vorbild in cfgparse.tcl
proc initTestingPrefs {} {
  global testing_prefs

  # allgemeine vordefinition
  # zur besseren auswertbarkeit gibt es fuer die felder noch
  #  ein is_disabled
  array set testing_prefs {
    gui_brite_top_topotypes			"1 Level: AS ONLY"
    gui_brite_top_topotypes_is_disabled		0
    gui_brite_top_executables			"Java"
    gui_brite_top_executables_is_disabled	0
    gui_brite_as_models				"Waxman"
    gui_brite_as_models_is_disabled		0
    gui_brite_as_nodeplacement			"Random"
    gui_brite_as_nodeplacement_is_disabled	0
    gui_brite_as_growthtype			"Incremental"
    gui_brite_as_growthtype_is_disabled 	0
    gui_brite_as_prefconn			"None"
    gui_brite_as_prefconn_is_disabled		0
    gui_brite_as_connlocali			"Off"
    gui_brite_as_connlocali_is_disabled		0
    gui_brite_as_bandwidthd			"Constant"
    gui_brite_as_bandwidthd_is_disabled		0
    gui_brite_as_hs				1000
    gui_brite_as_hs_is_disabled			0
    gui_brite_as_n				1000
    gui_brite_as_n_is_disabled			0
    gui_brite_as_ls				100
    gui_brite_as_ls_is_disabled			0
    gui_brite_as_alpha				0.15
    gui_brite_as_alpha_is_disabled		0
    gui_brite_as_beta				0.2
    gui_brite_as_beta_is_disabled		0
    gui_brite_as_p				0.6
    gui_brite_as_p_is_disabled			1
    gui_brite_as_q				0.2
    gui_brite_as_q_is_disabled			1
    gui_brite_as_gamma				-1
    gui_brite_as_gamma_is_disabled		0
    gui_brite_as_m				2
    gui_brite_as_m_is_disabled			0
    gui_brite_as_maxBW				1024.0
    gui_brite_as_maxBW_is_disabled		0
    gui_brite_as_minBW				10.0
    gui_brite_as_minBW_is_disabled		0
    gui_brite_router_models			"Waxman"
    gui_brite_router_models_is_disabled		0
    gui_brite_router_nodeplacement  		"Random"
    gui_brite_router_nodeplacement_is_disabled	0
    gui_brite_router_growthtype     		"Incremental"
    gui_brite_router_growthtype_is_disabled	0
    gui_brite_router_prefconn      		 "None"
    gui_brite_router_prefconn_is_disabled	0
    gui_brite_router_connlocali     		"Off"
    gui_brite_router_connlocali_is_disabled	0
    gui_brite_router_bandwidthd     		"Constant"
    gui_brite_router_bandwidthd_is_disabled	0
    gui_brite_router_hs           		1000
    gui_brite_router_hs_is_disabled		0
    gui_brite_router_n              		10000
    gui_brite_router_n_is_disabled		0
    gui_brite_router_ls             		100
    gui_brite_router_ls_is_disabled		0
    gui_brite_router_alpha          		0.15
    gui_brite_router_alpha_is_disabled		0
    gui_brite_router_beta           		0.2
    gui_brite_router_beta_is_disabled		0
    gui_brite_router_p				0.25
    gui_brite_router_p_is_disabled		1
    gui_brite_router_q				0.5
    gui_brite_router_q_is_disabled		1
    gui_brite_router_gamma			-1
    gui_brite_router_gamma_is_disabled		0
    gui_brite_router_m     		        2
    gui_brite_router_m_is_disabled		0
    gui_brite_router_maxBW          		1024.0
    gui_brite_router_maxBW_is_disabled		0
    gui_brite_router_minBW          		10.0
    gui_brite_router_minBW_is_disabled		0
    gui_brite_topdown_k				-1
    gui_brite_topdown_k_is_disabled		0
    gui_brite_topdown_rightMaxBW		1024.0
    gui_brite_topdown_rightMaxBW_is_disabled	0
    gui_brite_topdown_leftMaxBW			1024.0
    gui_brite_topdown_leftMaxBW_is_disabled	0
    gui_brite_topdown_rightMinBW		10.0
    gui_brite_topdown_rightMinBW_is_disabled	0
    gui_brite_topdown_leftMinBW			10.0
    gui_brite_topdown_leftMinBW_is_disabled	0
    gui_brite_topdown_ecm			"Random"
    gui_brite_topdown_ecm_is_disabled		0
    gui_brite_topdown_iebwd			"Constant"
    gui_brite_topdown_iebwd_is_disabled		0
    gui_brite_topdown_iabwd			"Constant"
    gui_brite_topdown_iabwd_is_disabled		0
    gui_brite_bottom_savedest			"/usr/share/core/out.cfg"
    gui_brite_bottom_execpath			"/home/hanstest/jw/gitbrite/brite/BRITE"
    gui_brite_bottom2_loadcfg			"/usr/share/core/out.cfg"
    gui_brite_bottom2_briteout			"/usr/share/core/topoOut"
    gui_brite_bottom3_loadbrite			"/usr/share/core/topoOut"
    gui_brite_bottom3_imnout			"/usr/share/core/topo.imn"
  }
}

