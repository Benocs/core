proc doStuff3 {} {


#  puts [pwd]
#  cd /home/jw/dateien/sw/brite/BRITE/Java
#  puts [pwd]

  set kill_string exec
  lappend kill_string killall
  lappend kill_string java
  lappend kill_string >@stdout 2>@stderr 
  {*}$kill_string


# Bsp von http://wiki.tcl.tk/1039
#  set start_bla exec
#  lappend start_bla /usr/bin/firefox
#  lappend start_bla -new-window https://www.google.com/
#  lappend start_bla >@stdout 2>@stderr
#  {*}$start_bla
}

