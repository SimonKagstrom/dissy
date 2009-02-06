######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      mips.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   MIPS arch specific stuff
##
## $Id: mips.py 14551 2007-03-29 16:55:13Z ska $
##
######################################################################
import dissy.architecture, re
from dissy.architecture import Architecture

REGISTER_REGEXP = "(?:[tsakv]{1}[0-9]{1})|sp|ra|fp|gp|at"
ADDRESS_REGEXP  = "[0-9,a-f,A-F]+"

mips_jumps = ['bgez',
              'bnez',
              'beqz',
              'blez',
              'bgez',
              'bltz',
              'bgtz',
              'bc1f',
              'bc1t',
              'beq',
              'bne',
              'b',
              'jal',
              'j',
              ]

mips_calls = ['jal']


class MipsArchitecture(Architecture):
    def __init__(self):
        Architecture.__init__(self, mips_jumps, mips_calls)
        self.jumpRegexp = re.compile("(?:(" + REGISTER_REGEXP + "),)+" + "(" + ADDRESS_REGEXP + ")");

    def getJumpDestination(self, insn, args):
        r = self.jumpRegexp.match(args)
        if r == None:
            return Architecture.getJumpDestination(self, insn, args)
        return Architecture.getJumpDestination(self, insn, r.group(2))
