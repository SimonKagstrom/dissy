######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Instruction class
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
from dissy.Entity import Entity, AddressableEntity

class Instruction(AddressableEntity):
    def __init__(self, function, address, encoding, insn, args):
        AddressableEntity.__init__(self, address = address, endAddress = address, baseAddress = function.baseAddress)
        self.function = function
        self.encoding = encoding
        self.insn = insn
        self.args = args
        self.outLinkAddress = None
        self.outLink = None
        arch = self.function.getFile().getArch()

        if arch.isJump(insn):
            val = arch.getJumpDestination(insn, args)
            if val != None:
                self.addLinkOut( val + self.baseAddress )

    def getFunction(self):
        return self.function

    def getOpcode(self):
        return self.insn

    def getArgs(self):
        if self.args != None:
            return self.args
        return ""

    def getOutLinkAddress(self):
        return self.outLinkAddress

    def getOutLink(self):
        return self.outLink

    def getInLinks(self):
        return self.inLink

    def hasLink(self):
        return self.outLinkAddress != None

    def addLinkIn(self, insn):
        pass # Implement this if needed
        #self.linksIn.append(insn)

    def addLinkOut(self, obj):
        self.outLinkAddress = obj

    def linkTo(self, other):
        self.outLink = other

    def link(self):
        if not self.hasLink():
            raise Exception
        other = self.function.lookup(self.getOutLinkAddress())
        if other:
            self.linkTo(other)
            other.addLinkIn(self)
        else:
            # External reference
            other = self.function.getFile().lookup(self.getOutLinkAddress())
            self.linkTo(other)
            if other == None:
                return False
            self.label = other.getLabel()
        return True

    def __str__(self):
        out = ("0x%08x " % self.address) + " " + str(self.insn)
        if self.args != None:
            out += str(" " * (20-len(out))) + str(self.args)
        return out
