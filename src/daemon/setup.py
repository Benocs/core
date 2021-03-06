# Copyright (c)2010-2012 the Boeing Company.
# See the LICENSE file included in this distribution.

#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

import os, glob
from distutils.core import setup
from core.constants import COREDPY_VERSION

# optionally pass CORE_CONF_DIR using environment variable
confdir = os.environ.get('CORE_CONF_DIR')
if confdir is None:
    confdir="/etc/core"

setup(name = "core-python",
      version = COREDPY_VERSION,
      packages = [
        "core",
        "core.addons",
        "core.api",
        "core.emane",
        "core.misc",
        "core.bsd",
        "core.netns",
        "core.phys",
        "core.xen",
        "core.services",
        ],
      data_files = [("sbin", glob.glob("sbin/core*")),
                    ("bin", glob.glob("bin/core*")),
                    (confdir, ["data/core.conf"]),
                    (confdir, ["data/xen.conf"]),
                    ("share/core/examples", ["examples/controlnet_updown"]),
                    ("share/core/examples",
                     glob.glob("examples/*.py")),
                    ("share/core/examples/netns",
                     glob.glob("examples/netns/*[py,sh]")),
                    ("share/core/examples/services",
                     glob.glob("examples/services/*")),
                    ("share/core/examples/myservices",
                     glob.glob("examples/myservices/*")),
                    ],
      description = "Python components of CORE",
      url = "https://github.com/Benocs/core/",
      author = "Benocs",
      author_email = "core-dev@benocs.com",
      license = "BSD",
      long_description="Python scripts and modules for building virtual " \
          "emulated networks.")
