# various CORE helper services that implement data storage functions
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

class Data():
    _data_dir = '/var/lib/core'
    _files = ()

    @classmethod
    def populateDirectory(cls, node, directory, services):
        print(('populateDirectory: %s ' % str(directory)))
        if directory == cls._dirs[1]:
            cls.getFiles(node)

    @classmethod
    def getFiles(self, node, allFiles = True, filelist = None):
        if allFiles:
            filelist = self._files
        elif filelist is None:
            filelist = []

        print(('getFiles: node: %s, allFiles: %s, filelist: %s' % (str(node), str(allFiles),
                str(filelist))))

        for file, dst, hardlink in filelist:
            head, filename = os.path.split(file)
            print(('creating %s-link: "%s" -> "%s"' % (("hard" if hardlink else "soft"), file, dst)))
            print(('  file: %s, dstfilename: %s, hardlink: %s' % (str(file),
                    str(os.path.join(dst, filename)), str(hardlink))))
            node.nodefilelink(os.path.join(self._data_dir, file), os.path.join(dst, filename), hardlink)

