# various CORE helper services that implement data storage functions
#
#
# Copyright (c) 2014 Benocs GmbH
#
# author: Robert Wuttke <robert@benocs.com>
#
# See the LICENSE file included in this distribution.
#

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

