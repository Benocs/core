#!/bin/bash
#
# (c)2010-2012 the Boeing Company
#
# author:	Jeff Ahrenholz <jeffrey.m.ahrenholz@boeing.com>
#
# Bootstrap the autoconf system.
#

if [ x$1 = x ]; then		# PASS
  echo "Bootstrapping the autoconf system..."
# echo "  These autotools programs should be installed for this script to work:"
# echo "    aclocal, libtoolize, autoheader, automake, autoconf"
  echo "(Messages below about copying and installing files are normal.)"
elif [ x$1 = xclean ]; then 	# clean - take out the trash
  echo "Cleaning up the autoconf mess..."
  rm -rf autom4te.cache config BSDmakefile 
  exit 0;
else				# help text
  echo "usage: $0 [clean]"
  echo -n "  Use this script to bootstrap the autoconf build system prior to "
  echo "running the "
  echo "  ./configure script."
  exit 1;
fi

# try to keep everything nice and tidy in ./config
if ! [ -d "config" ]; then
  mkdir config
fi

# on FreeBSD, discourage use of make
UNAME=`uname`
if [ x${UNAME} = xFreeBSD ]; then
	echo "all:" > BSDmakefile
	echo '	@echo "Please use GNU make instead by typing:"' >> BSDmakefile
	echo '	@echo "		gmake"' >> BSDmakefile
	echo '	@echo ""' >> BSDmakefile
fi

fix_automake() {
  for aclocal in aclocal.m4*; do
    echo "patching $aclocal.."
    grep -n "PYTHON_VERSION\/site-packages" "$aclocal"
    sed -i -e 's/PYTHON_VERSION\/site-packages/PYTHON_VERSION\/dist-packages/' "$aclocal"
    echo "done patching $aclocal:"
    grep -n "PYTHON_VERSION\/dist-packages" "$aclocal"
  done
}

fix_configure() {
  # TODO: FIXME: this is not how it's supposed to be
  sed -i -e 's/pythondir=\$am_cv_python_pythondir/pythondir=\$PYTHON_PREFIX\/lib\/python\$PYTHON_VERSION\/dist-packages/' configure
  sed -i -e 's/pyexecdir=\$am_cv_python_pyexecdir/pyexecdir=\$PYTHON_PREFIX\/lib\/python\$PYTHON_VERSION\/dist-packages/' configure
}

# bootstrapping
echo "(1/4) Running aclocal..." && aclocal -I config \
  && fix_automake \
  && echo "(2/4) Running autoheader..." && autoheader \
  && echo "(3/4) Running automake..." \
	&& automake --add-missing --copy --foreign \
  && echo "(4/4) Running autoconf..." && autoconf \
  && fix_configure \
  && echo "" \
  && echo "You are now ready to run \"./configure\"."
