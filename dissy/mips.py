######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   MIPS arch specific stuff
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
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

instr_descriptions = {
    'lbu': 'Load Unsigned Byte',
    'lb': 'Load signed Byte',
    'li': 'Load Immediate value to destination register',
    'lui' : 'Load Upper Immediate (set destination to v << 16)',
    'move' : 'Copy between registers',
    'jal' : 'Jump And Link, jump to destination and store return address in ra (r31)',
    'or' : 'Bitwise or',
    'sb' : 'Store Byte to memory',
    'sw' : 'Store 32-bit word to memory',
    'sh' : 'Store 16-bit word to memory',
    'lb' : 'Load Byte from memory, signed',
    'lw' : 'Load 32-bit value from memory',
    'lh' : 'Load 16-bit value from memory, signed',
    'lbu' : 'Load 16-bit value from memory, unsigned',
    'lhu' : 'Load 16-bit value from memory, unsigned',
}


class MipsArchitecture(Architecture):
    def __init__(self):
        Architecture.__init__(self, mips_jumps, mips_calls)
        self.jumpRegexp = re.compile("(?:(" + REGISTER_REGEXP + "),)+" + "(" + ADDRESS_REGEXP + ")");

    def getJumpDestination(self, address, insn, args):
        r = self.jumpRegexp.match(args)
        if r == None:
            return Architecture.getJumpDestination(self, address, insn, args)
        return Architecture.getJumpDestination(self, address, insn, r.group(2))

    def getInstructionInfo(self, instruction):
        opcode = instruction.getOpcode()
        args = str(instruction.getArgs())
        description = instr_descriptions.get(instruction.getOpcode(), '')

        return {'shortinfo': opcode + " " + args,
                'description': description,
                }
