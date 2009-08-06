######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Describes one file
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import cgi, os, sys, re
import cPickle as pickle

sys.path.append(".")
import dissy, dissy.architecture

from dissy.Function import *
from dissy.Instruction import *
from dissy.Data import *
from dissy.Entity import AddressableEntity

ADDRESS_REGEXP  = "[0-9,a-f,A-F]+"
FUNCTION_REGEXP = "(?:[.]*)[_,0-9,a-z,A-Z,\:,\*,\,\(,\), ,<,>,~,\.]+"

symbolRegexp = re.compile("(" + ADDRESS_REGEXP + ")* *(" + ADDRESS_REGEXP + ")* ([A,B,C,D,G,I,N,R,S,T,U,V,W,a,b,c,d,g,i,n,r,s,t,u,v,w,-,?]{1}) ("+ FUNCTION_REGEXP + "){1}")

# Followed by size, but let's just skip it
linuxKernelCrashRegexp = re.compile("(" + FUNCTION_REGEXP + "){1}" + "\+[0x]*(" + ADDRESS_REGEXP + "){1}")

TYPE_UNDEFINED = 0
TYPE_TEXT = 1
TYPE_RODATA = 2
TYPE_DATA = 3
TYPE_BSS  = 4

typeToClass = {
    TYPE_TEXT : Function,
    TYPE_RODATA : RoData,
    TYPE_DATA : Data,
    TYPE_BSS : Bss,
}

def getObjType(s):
    if s in ('u', 'U'):
        return TYPE_UNDEFINED
    elif s in ('d', 'D'):
        return TYPE_DATA
    elif s in ('r', 'R'):
        return TYPE_RODATA
    elif s in ('b', 'B', 's', 'S', 'c', 'C'):
        return TYPE_BSS
    elif s in ('t', 'T'):
        return TYPE_TEXT
    return TYPE_DATA


class BaseFile(AddressableEntity):
    def __init__(self, baseAddress = 0):
        global global_file
        AddressableEntity.__init__(self, baseAddress = baseAddress)
        self.symbols = []
        self.functions = []
        self.data = []
        self.arch = "intel"
        global_file = self

    def lookup_int(self, address):
        for sym in self.symbols:
            extents = sym.getExtents()
            if address >= extents[0] and address < extents[1]:
                return sym
        return None

    def link(self):
        for fn in self.functions:
            unresolved = fn.link()
            for insn in unresolved:
                other = self.lookup(insn.getAddress())
                if other:
                    insn.linkTo(other)

    def lookup_str(self, label):
        for sym in self.symbols:
            if label == sym.getLabel():
                return sym
        return None

    def lookup(self, param):
        "Lookup a label or an address"
        if isinstance(param, long):
            return self.lookup_int(param)
        return self.lookup_str(param)

    def getArch(self):
        return self.arch

    def hasSymbols(self):
        return True

    def parse(self):
        """Parses the output of 'nm', to get the list of symbols"""
        lines = self.getNmLines()
        for line in lines:
            r = symbolRegexp.match(line)
            if r == None:
                continue
            address = 0
            size = 0
            if r.group(1) != None:
                address = long("0x" + r.group(1), 16)
            if r.group(2) != None:
                size = long("0x" + r.group(2), 16)
            objType = getObjType(r.group(3))
            label = cgi.escape(r.group(4))

            if size == 0:
                idx = lines.index(line) + 1
                if idx < len(lines)-1:
                    # The size is the next real symbol's line.adr - this line.adr
                    s = symbolRegexp.match(lines[idx])
                    while idx < len(lines)-1 and s == None or (s and s.group(1) == None):
                        idx = idx + 1
                        s = symbolRegexp.match(lines[idx])

                    nextAdr = long("0x" + s.group(1), 16)
                    size = nextAdr - address
                else:
                    # FIXME: This is a bug - the last symbol will be too small.
                    # This can be fixed by e.g., using the section size
                    size = 0

            if objType == TYPE_UNDEFINED:
                continue

            if objType == TYPE_TEXT:
                sym = typeToClass[objType](self, address, label, size)
                self.functions.append(sym)
                self.symbols.append(sym)
#            else:
#                sym = typeToClass[objType](self, address, label, size)
#                self.data.append(sym)
        
    def parseNoSymbols(self):
        """Parses the output of objdump, and create the functions"""
        lines = self.getObjdumpLines()
        callDests = []
        for line in lines:
            r = insnRegExp.match(line)
            if r != None:
                if self.arch.isCall(r.group(3)):
                    dst = self.arch.getJumpDestination(r.group(3), r.group(4))
                    if dst != None:
                        callDests.append(dst)
        # Sort the calls
        callDests.sort()
        count = 0
        for call in callDests[:-1]:
            next = callDests[callDests.index(call)+1]
            if next-call == 0:
                # Empty
                continue
            fn = Function(self, call, "func%d" % (count), next-call)
            # This has not been prepared yet...
            fn.stream = None
            self.functions.append(fn)
            count = count + 1

    def getFunctions(self):
        return self.functions

    def getData(self):
        return self.functions

class File(BaseFile):
    def __init__(self, filename=None, baseAddress = 0):
        BaseFile.__init__(self, baseAddress = baseAddress)
        self.filename = filename

        if filename != None:
            self.arch = dissy.architecture.getArchitecture(self.getArchStr())
            if self.hasSymbols():
                self.parse()
            else:
                self.parseNoSymbols()

    def getArchStr(self):
        "Get the architecture of the file"
        arch = "intel" # Assume Intel architecture
        f = os.popen("%s -h --wide %s" % (config.readelf, self.filename))
        for line in f:
            words = line.split()
            if len(words) >= 2 and words[0] == "Machine:":
                arch = words[1].lower()
                break
        f.close()
        return arch

    def getNmLines(self):
        f = os.popen("%s --numeric-sort --demangle --print-size %s" % (config.nm, self.filename))
        lines = f.readlines()
        f.close()
        return lines

    def getObjdumpLines(self):
        "Parse the functions from this file (without symbols)"
        f = os.popen("%s --disassemble --demangle --disassemble-zeroes %s" % (config.objdump, self.filename))
        for line in f:
            yield line
        f.close()

    def getFunctionObjdump(self, funclabel, start, end):
        s = "%s --wide --demangle --disassemble-zeroes --source --start-address=0x%Lx --stop-address=0x%Lx %s" % (config.objdump, start, end, self.filename)
        f = os.popen(s)
        for line in f:
            yield line
        f.close()

    def getObjdumpSourceLines(self):
        s = "%s --wide --demangle --disassemble-zeroes --source %s" % (config.objdump, self.filename)
        f = os.popen(s)
        for line in f:
            yield line
        f.close()

    def __str__(self):
        out = "%s: " % (self.filename)
        for fn in self.functions:
            out = out + str(fn)
        return out

    def toExportedFile(self):
        expfile = ExportedFile()
        expfile.archStr = self.getArchStr()
        expfile.objdumpLines = list(self.getObjdumpLines())
        expfile.objdumpSourceLines = list(self.getObjdumpSourceLines())
        expfile.nmLines = list(self.getNmLines())
        return expfile

class ExportedFile(BaseFile):
    def __init__(self, filename=None, baseAddress = 0):
        BaseFile.__init__(self, baseAddress = baseAddress)
        self.filename = filename

        self.archStr = "intel"
        self.objdumpLines = []
        self.nmLines = []
        self.objdumpSourceLines = []

        if filename != None:
            f = open(filename, 'rb')
            self.archStr = pickle.load(f)
            self.nmLines = pickle.load(f)
            self.objdumpLines = pickle.load(f)
            self.objdumpSourceLines = pickle.load(f)
            f.close()

            self.arch = dissy.architecture.getArchitecture(self.getArchStr())
            if self.hasSymbols():
                self.parse()
            else:
                self.parseNoSymbols()

    def getArchStr(self):
        return self.archStr

    def getNmLines(self):
        return self.nmLines

    def getObjdumpLines(self):
        return self.objdumpLines

    def getFunctionObjdump(self, funclabel, start, end):
        infunc = False
        startlinere = re.compile("^[0]*%Lx <%s>:" % (start, funclabel))
        endlinere = re.compile("^[0]*%Lx <.*>:" % (end))
        lastline = None
        for line in self.objdumpSourceLines:
            if not infunc:
                r = startlinere.match(line)
                if r != None:
                    infunc = True
                    lastline = line
            elif infunc:
                r = endlinere.match(line)
                if r != None:
                    return
                else:
                    yield lastline
                    lastline = line
        #this means we reached the end of the dump, also yield the last line
        if lastline:
            yield lastline

    def saveTo(self, f):
        pickle.dump(self.archStr, f, -1)
        pickle.dump(self.nmLines, f, -1)
        pickle.dump(self.objdumpLines, f, -1)
        pickle.dump(self.objdumpSourceLines, f, -1)

    def __str__(self):
        out = "%s: " % (self.filename)
        for fn in self.functions:
            out = out + str(fn)
        return out

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Arg: filename (ELF)"
        sys.exit(1)
    f = File(sys.argv[1])
    f.parse()


# Module-global file object
global_file = None

def getArchStr(): return global_file.getArchStr()

def lookup(param): return global_file.lookup(param)

def getFunctions(): return global_file.getFunctions()

def getData(): return global_file.getData()
