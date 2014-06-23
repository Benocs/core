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

setup(name = "coretopogen",
      version = COREDPY_VERSION,
      packages = [
        "coretopogen",
        ],
      data_files = [("bin", glob.glob("bin/core-*")),
                    (confdir, ["files/brite.augment"]),
                    (confdir, ["files/brite.nodemap"]),
                    ],
      description = "Topology generator for CORE",
      url = "",
      author = "Benocs",
      author_email = "robert@benocs.com",
      license = "BSD",
      long_description="Python scripts and modules for generating network " \
          "topologies to be used by CORE.")
