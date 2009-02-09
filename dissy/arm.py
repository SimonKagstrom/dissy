######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Arm arch specific stuff
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import sys, architecture
from dissy.architecture import Architecture

arm_jumps = ['b',
             'bcc',
             'bl',
             'ble',
             'bne',
             'bleq',
             'blt',
             'bgt',
             'beq',
             'bcs',
             ]
arm_calls = ['bl']
arm_conditionflag_setters = ['cmp'] + \
    [i + "s" for i in 
    ['mul', 'mla', 'umull', 'umlal', 'smull',
    'smlal', 'mov', 'mvn', 'asr', 'lsl', 'lsr', 'ror', 'rrx',] #TODO more
    ]
arm_conditionflag_users = ['']

arm_instr_descriptions = {
    'cmp': 'Compare two values, and sets the condition flags',
    'adc': 'Add with carry',
    'add': 'Add',
    'sub': 'Subtract',
    'and': 'Logical and',
    'bic': 'Bit Clear',
    'bal': 'Unconditional Branch',
    'blal': 'Unconditional Branch and Link',
    'mov': 'Move',
    'bx': """Branch and eXchange 
PC := Rm""",
    'bl': """Branch with Link
LR := Address of next instruction, PC := label""",
    'push': """Push on the stack.
Canonical form of "stmdb SP!, <reglist>\"""",
    'pop': """Pop from the stack.
Canonical form of "ldm SP!, <reglist>\"""",
    'asr': 'Arithmetic Shift Right',
    'mul': 'Multiply',
    'muls': 'Multiply and set condition flags',
    'mla': 'Multiply and Accumulate',
    'mls': 'Multiply and Subtract',
}

arm_lists_inited = False
if not arm_lists_inited:
    branch_instructions = {
        'b': """Branch on %s
PC := label, label is this instruction +/-32Mb""", 
        'bx': """Branch and eXchange on %s
PC := Rm""", 
        'bl': """Branch and Link on %s""",
        'mov': """Move on %s""",
        }
    conditions = {
        'cs': 'Carry Set',
        'cc': 'Carry Clear',
        'eq': 'Equal (Zero Set)',
        'ne': 'Not Equal (Zero Clear)',
        'vs': 'Overflow Set',
        'vc': 'Overflow Clear',
        'gt': 'Signed Greater Than',
        'lt': 'Signed Less Than',
        'ge': 'Signed Greater than or Equal',
        'le': 'Signed Less than or Equal',
        'pl': 'Plus (Positive)',
        'mi': 'Minus (Negative)',
        'hi': 'Unsigned Higher Than',
        'lo': 'Unsigned Lower Than',
        'hs': 'Unsigned Higher or Same',
        'ls': 'Unsigned Lower or Same',
        }
    for i in branch_instructions:
        for c in conditions:
            arm_instr_descriptions[i + c] = branch_instructions[i] % (conditions[c])
            arm_conditionflag_users += [i + c]
    arm_lists_inited = True

class ArmArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, arm_jumps, arm_calls, 
            arm_conditionflag_setters, arm_conditionflag_users)

    def getInstructionInfo(self, instruction):
        opcode = instruction.getOpcode()
        args = str(instruction.getArgs())
        description = arm_instr_descriptions.get(instruction.getOpcode(), '')

        return {'shortinfo': opcode + " " + args,
                'description': description,
                }
