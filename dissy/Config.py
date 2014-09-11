######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Configuration storage
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import cPickle, os, os.path, sys

PROGRAM_NAME="Dissy"
PROGRAM_VERSION="10"
PROGRAM_URL="http://dissy.googlecode.com"

def getBasePath():
    dn = os.path.dirname(sys.argv[0])
    base = os.path.dirname(os.path.realpath(dn))

    if base == None:
	base = "/usr/local/"
    return base

bp = getBasePath()
pn = PROGRAM_NAME.lower()
pathsToSearch = [bp + "/share/%s" % pn, '/usr/local/share/%s' % pn,
                     '/usr/share/%s' % pn]

def lookupFile(name):
    for path in pathsToSearch:
        fullPath = "%s/%s" % (path, name)

        try:
            st = os.lstat(fullPath)
            return fullPath
        except:
            pass
    return None


class Config:
    def __init__(self):
        self.configfile = os.path.expanduser("~/.dissy/config.dump")

        self.defaults = {}

        self.defaults["width"] = 900
        self.defaults["height"] = 600
        self.defaults["markupFgColor"] = "red"
        self.defaults["insnFgColor"] = "blue"
        self.defaults["highLevelCodeFgColor"] = "grey50"
        self.defaults["showHighLevelCode"] = True
        self.defaults["showInstructionInformationBox"] = True
        self.defaults["objdump"] = "objdump"
        self.defaults["readelf"] = "readelf"
        self.defaults["nm"] = "nm"
        self.defaults["version"] = PROGRAM_VERSION

        self.restoreAllDefaults()

    def restoreAllDefaults(self):
        self.width = self.getDefault("width")
        self.height = self.getDefault("height")
        self.markupFgColor = self.getDefault("markupFgColor")
        self.insnFgColor = self.getDefault("insnFgColor")
        self.highLevelCodeFgColor = self.getDefault("highLevelCodeFgColor")
        self.showHighLevelCode = self.getDefault("showHighLevelCode")
        self.showInstructionInformationBox = self.getDefault("showInstructionInformationBox")
        self.objdump = self.getDefault("objdump")
        self.readelf = self.getDefault("readelf")
        self.nm = self.getDefault("nm")

    def copy(self, other):
        try:
            self.width = other.width
            self.height = other.height
        except:
            pass
        self.markupFgColor = other.markupFgColor
        self.insnFgColor = other.insnFgColor
        self.highLevelCodeFgColor = other.highLevelCodeFgColor
        self.showHighLevelCode = other.showHighLevelCode
        self.showInstructionInformationBox = getattr(other, "showInstructionInformationBox", True)
        self.objdump = other.objdump
        self.readelf = other.readelf
        self.nm = other.nm

    def getFromEnvironment(self):
        # allow the "OBJDUMP", "READELF", "NM" environment variables to
        # override the default executables used
        self.objdump = os.getenv("OBJDUMP", self.objdump)
        self.readelf = os.getenv("READELF", self.readelf)
        self.nm = os.getenv("NM", self.nm)

    def getDefault(self, which):
        return self.defaults[which]

    def load(self):
        try:
            f = open(self.configfile)
            other = cPickle.load(f)
            f.close()
            self.copy(other)
        except IOError:
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.configfile), 0700)
        except OSError:
            # Already exists
            pass
        f = open(self.configfile, "w")
        cPickle.dump(self, f)
        f.close()

config = Config()

# Load the old configuration
config.load()
config.getFromEnvironment()
