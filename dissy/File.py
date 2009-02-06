######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Describes one file
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import cgi, os, sys

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


class File(AddressableEntity):
    def __init__(self, filename=None, baseAddress = 0):
        AddressableEntity.__init__(self, baseAddress = baseAddress)
        self.symbols = []
        self.functions = []
        self.data = []
        self.filename = filename
        self.arch = "intel"
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

    def lookup_int(self, address):
        for sym in self.symbols:
            extents = sym.getExtents()
            if address >= extents[0] and address < extents[1]:
                return sym
        return None

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

    def link(self):
        for fn in self.functions:
            unresolved = fn.link()
            for insn in unresolved:
                other = self.lookup(insn.getAddress())
                if other:
                    insn.linkTo(other)

    def parse(self):
        "Parse the functions from this file (with symbols)"

        f = os.popen("%s --numeric-sort --demangle --print-size %s" % (config.nm, self.filename))
        lines = f.readlines()
        f.close()

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
                idx = lines.index(line)
                if idx < len(lines)-1:
                    # The size is next line.adr - this line.adr
                    s = symbolRegexp.match(lines[idx+1])
                    if s == None or s and s.group(1) == None:
                        # Nope, doesn't work...
                        continue

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
        "Parse the functions from this file (without symbols)"

        callDests = []
        f = os.popen("%s --disassemble --demangle %s" % (config.objdump, self.filename))
        for line in f:
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
        f.close()

    def getFunctions(self):
        return self.functions

    def getData(self):
        return self.functions

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
