######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Describes data symbols
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import re, os, cgi, curses.ascii

from dissy.Config import config
from dissy.Entity import Entity, AddressableEntity
from dissy.StrEntity import StrEntity

class DataBase(AddressableEntity):
    def __init__(self, fileContainer, address, label, size=0):
        AddressableEntity.__init__(self, address = address, endAddress = address + size, baseAddress = fileContainer.baseAddress)
        self.label = label
        self.file = fileContainer
        self.data = []
        self.string = ""
        self.stream = None
        self.type = "Unknown"

    def parse(self):
        pass

    def toNumericValue(self):
        val = 0
        if len(self.data) in (1,2,4,8):
            for i in range(0, len(self.data)):
                val = val + self.data[i] << (len(self.data) - i)*8
        return val

    def toBytes(self):
        return self.data

    def toString(self):
        return self.string

class Data(DataBase):
    def __init__(self, fileContainer, address, label, size=0):
        DataBase.__init__(self, fileContainer, address, label, size)
        self.type = "Initialized data"

    def parse(self):
        extents = self.getExtents()
        s = "%s --wide --demangle --full-contents --start-address=0x%x --stop-address=0x%x %s" % (config.objdump, extents[0], extents[1], self.file.filename)
        self.stream = os.popen(s)
        for line in self.stream:
            # Weed away some unneeded stuff
            if line.startswith("Contents of section ") or line.startswith("%s: " % (self.file.filename)):
                continue
            if line.strip() == "":
                continue

            words = line.split()
            for word in words[1:max(4, len(words))]:
                for i in range(0, len(word), 2):
                    try:
                        val = int(word[i:i+2], 16)
                        self.data.append(val)
                    except:
                        # For "short" data
                        continue
                    if curses.ascii.isprint(val):
                        self.string += "%c" % curses.ascii.ascii(val)
                    else:
                        self.string += "."
        self.stream.close()

class Bss(DataBase):
    def __init__(self, fileContainer, address, label, size=0):
        DataBase.__init__(self, fileContainer, address, label, size)
        self.type = "Uninitialized data"

    def parse(self):
        size = self.getSize()
        self.data = [ 0 ] * size
        self.string = "." * size

class RoData(Data):
    def __init__(self, fileContainer, address, label, size=0):
        Data.__init__(self, fileContainer, address, label, size)
        self.type = "Read-only data"
