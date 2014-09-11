######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Entity (address, size etc.)
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
class Entity:
    def __init__(self):
        pass


class AddressableEntity(Entity):
    def __init__(self, address=0, baseAddress = 0, endAddress = 0):
        self.label = ""
        self.address = address + baseAddress
        self.baseAddress = baseAddress
        if endAddress == 0:
            self.endAddress = self.address
        else:
            self.endAddress = endAddress + baseAddress

    def getLabel(self):
        return self.label

    def getExtents(self):
        "Return the extents of this function"
        return (self.address - self.baseAddress, self.endAddress - self.baseAddress)

    def setSize(self, size):
        "Set the size of this entity"
        self.endAddress = self.address + size

    def getSize(self):
        return self.endAddress - self.address
