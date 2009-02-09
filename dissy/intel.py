######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Intel arch specific stuff
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import sys, architecture
from dissy.architecture import Architecture

intel_jumps = ['jmp',
               'call'
               ]
intel_calls = ['call']

intel_conditionflag_setters = ['cmp', 'cmpb', 'cmps', 'cmpw', 'cmpl', 'cmpq', 'test']

intel_conditionflag_users = ['']

intel_instr_descriptions = {
    'push': 'Push Word onto Stack',
    'pushl': 'Push Long onto Stack',
    'mov': 'Move',
    'movl': 'Move Long',
    'cmp': 'Compare',
    'cmpb': 'Compare Byte',
    'lea': 'Load Effective Address',
    'add': 'Add',
    'jmp': 'Unconditional Jump',
    'pop': 'Pop Word off Stack',
    'ret': 'Return from Procedure',
    'sub': 'Subtract',
    'xor': 'eXclusive Or',
    'and': 'Logical And',
    'nop': 'NoOp',
    'call': 'Procedure Call',
    'hlt': 'Halt',
    'test': """Test for Bit Pattern
Performs a logical AND of the two operands, updating the condition flags without saving the results""",
    'leave': 'Restore stack for procedure exit',
    'xchg': 'Exchange',
    'sar': 'Shift Arithmetic Right',
    'sal': 'Shift Arithmetic Left',
    'shr': 'Shift Logical Right',
    'shl': 'Shift Logical Left',
}

intel_lists_inited = False
if not intel_lists_inited:
    conditional_instructions = {
        'j': "Jump if %s",
    }
    conditions = {
        'a': 'Above',
        'ae': 'Above or Equal',
        'b': 'Below',
        'be': 'Below or Equal',
        'c': 'Carry set',
        'cxz': 'CX Zero',
        'e': 'Equal',
        'g': 'Greater (Signed)',
        'ge': 'Greater or Equal (Signed)',
        'l': 'Less (Signed)',
        'le': 'Less or Equal (Signed)',
        'na': 'Not Above',
        'nae': 'Not Above or Equal',
        'nb': 'Not Below',
        'nbe': 'Not Below or Equal',
        'nc': 'Not Carry',
        'ne': 'Not Equal',
        'ng': 'Not Greater (Signed)',
        'nge': 'Not Greater or Equal (Signed)',
        'nl': 'Not Less (Signed)',
        'nle': 'Not Less or Equal (Signed)',
        'no': 'Not Overflow (Signed)',
        'np': 'No Parity',
        'ns': 'Not Signed (Signed)',
        'nz': 'Not Zero',
        'o': 'Overflow (Signed)',
        'p': 'Parity',
        'pe': 'Parity Even',
        'po': 'Parity Odd',
        's': 'Signed (Signed)',
        'z': 'Zero',

    }
    for i in ['j']:
        for c in conditions:
            intel_instr_descriptions[i + c] = conditional_instructions[i] % (conditions[c])
            intel_conditionflag_users += [i + c]
            intel_jumps += [i + c]


class IntelArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, intel_jumps, intel_calls,
            intel_conditionflag_setters, intel_conditionflag_users)

    def getInstructionInfo(self, instruction):
        opcode = instruction.getOpcode()
        args = str(instruction.getArgs())
        description = intel_instr_descriptions.get(instruction.getOpcode(), '')

        return {'shortinfo': opcode + " " + args,
                'description': description,
                }
