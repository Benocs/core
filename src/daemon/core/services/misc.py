# various stub CORE services that exist solely to indicate different service
# classes a node implements
#
# Copyright (C) 2014 Robert Wuttke <robert@benocs.com>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

import os

from core.service import CoreService, addservice
from core.misc.utils import *

from core.services import utility

class MiscFlag(CoreService):
    _name = "misc flags"
    _group = "Misc Flags"
    _depends = ()

class BareMetal(MiscFlag):
    _name = "BareMetal"
    _meta = "This is a bare metal machine"

addservice(BareMetal)
