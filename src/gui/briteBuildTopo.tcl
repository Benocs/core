
# fkt startet brite im java consolen modus mit standard argumenten
#   TODO argumente variabel machen .. vielleicht auch in anderes
#       brite fenster integrieren--
# ausfuehrungsort: /home/jw/dateien/sw/brite/BRITE/Java
# ausfuehrungsparamter: java -Xms????m -Xmx????M Main.Brite ../GUI_GEN.conf outfile seed_file 
# zuaetzlich >@stdout 2>@stderr zur ausgabe von fehlern und ausgaben in
#     die console und nicht in die rueckgabe von core
proc doStuff2 {} {

  puts >> DEPRECATED

#  puts [pwd]
  cd /home/jw/dateien/sw/brite/BRITE/Java
#  puts [pwd]

  set exec_string exec
  lappend exec_string java
  lappend exec_string -Xms2048M -Xmx2048M
  lappend exec_string Main.Brite
#  lappend exec_string ../GUI_GEN.conf
  lappend exec_string /usr/share/core/out
  lappend exec_string ../outfile
  lappend exec_string seed_file
  lappend exec_string >@stdout 2>@stderr &
  {*}$exec_string


# Bsp von http://wiki.tcl.tk/1039
#  set start_bla exec
#  lappend start_bla /usr/bin/firefox
#  lappend start_bla -new-window https://www.google.com/
#  lappend start_bla >@stdout 2>@stderr
#  {*}$start_bla
}
