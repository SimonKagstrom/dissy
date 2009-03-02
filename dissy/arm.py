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
    'smull': """Signed Multiply Long
%(arg1)s,%(arg2)s := signed(%(arg3)s * %(arg4)s)""",
    'ldr': 'Load (from memory to register)',
    'str': 'Store (from register to memory)',
    'lsl': 'Logical Shift Left',
    'lsls': 'Logical Shift Left and set condition flags',
    'lsr': 'Logical Shift Right',
    'lsr': 'Logical Shift Right and set condition flags',
    'rsb': 'Reverse Subtract',
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

arm_lists_inited = False
if not arm_lists_inited:
    conditional_instructions = {
        'b': """Branch on %s
PC := label, label is this instruction +/-32Mb""",
        'bx': """Branch and eXchange on %s
PC := Rm
Change to Thumb mode if Rm[0] is 1, change to ARM mode if Rm[0] is 0""",
        'bl': """Branch and Link on %s""",
        'mov': """Move on %s""",
        'add': """Add on %s""",
        'sub': """Subtract on %s""",
        }

    for i in conditional_instructions:
        for c in conditions:
            arm_instr_descriptions[i + c] = conditional_instructions[i] % (conditions[c])
            arm_conditionflag_users += [i + c]
    arm_lists_inited = True

class ArmArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, arm_jumps, arm_calls,
            arm_conditionflag_setters, arm_conditionflag_users)

    def getInstructionInfo(self, instruction):
        opcode = instruction.getOpcode()
        args = str(instruction.getArgs())

        args_list = args.split(", ")
        args_dict = dict(
            zip(['arg' + str(i) for i in range(1, len(args_list)+1)],
                args_list))
        description = arm_instr_descriptions.get(instruction.getOpcode(), '')

        return {'shortinfo': opcode + " " + args,
                'description': description % args_dict,
                }

    def parseArguments(self, instr):
        """Parses an argument string, into a two-tuple, containing:
            * A list of the registers read in this instruction
            * A list of the registers written to in this instruction"""

        def parseComSepList(lstr):
            ret = []
            tmp = ""
            stack = []
            for c in lstr:
                if c in "{[":
                    stack += [c]
                    tmp += c
                elif c in "]}":
                    tmp += c
                    c2 = stack.pop()
                    if c == "]" and c2 == "[" or \
                        c == "}" and c2 == "{":
                        ret += [tmp]
                        tmp = ""
                    else:
                        raise ValueError("unbalanced parenthesis")
                elif c == ' ':
                    pass
                elif stack == [] and c == ',':
                    ret += [tmp]
                    tmp = ""
                elif stack == []:
                    tmp += c
                else:
                    tmp += c
            if tmp:
                ret += [tmp]
            return ret
        def isRegister(s):
            if s in ['r' + str(i) for i in range(0, 16)]: #r0..r15
                return True
            if s in ['sl', #r10 = gcc "got pointer"?
                    'fp', #r11 = gcc frame pointer
                    'ip', #r12 = gcc "scratch register"?
                    'sp', #r13, stack pointer
                    'lr', #r14, link register
                    'pc']: #r15, program counter
                return True
            return False

        args = parseComSepList(instr.args)
        if instr.getOpcode()[:3] == 'cmp':
            regwrite = []
            regread = [a for a in args if isRegister(a)]
        elif instr.getOpcode()[:3] in ['sub', 'add', 'lsl', 'asr', 'rsb', 'mov']:
            regwrite = [args[0]]
            regread = [a for a in args[1:] if isRegister(a)]
        #branches
        elif instr.getOpcode() in ['b' + c for c in conditions.keys() + ['']]:
            regwrite = ['pc']
            regread = []
        elif instr.getOpcode() in ['bl' + c for c in conditions.keys() + ['']]:
            regwrite = ['pc', 'lr']
            regread = []
        elif instr.getOpcode() in ['bx' + c for c in conditions.keys() + ['']]:
            regwrite = ['pc']
            regread = [args[0]]
        elif instr.getOpcode() in ['blx' + c for c in conditions.keys() + ['']]:
            regwrite = ['pc']
            regread = isRegister(args[0]) and [args[0]] or []
        #load
        elif instr.getOpcode() in ['ldr' + c for c in conditions.keys() + ['']]:
            regwrite = [args[0]]
            regread = []
            if args[1].startswith('['):
                offsetl = parseComSepList(args[1][1:-1])
                regread = [r for r in offsetl if isRegister(r)]
        #store
        elif instr.getOpcode() in ['str' + c for c in conditions.keys() + ['']]:
            regwrite = []
            regread = [args[0]]
            if args[1].startswith('['):
                offsetl = parseComSepList(args[1][1:-1])
                regread += [r for r in offsetl if isRegister(r)]
        #push
        elif instr.getOpcode() in ['push' + c for c in conditions.keys() + ['']]:
            regwrite = ['sp']
            regread = ['sp']
            reglist = parseComSepList(args[0][1:-1])
            regread += reglist
        elif instr.getOpcode() in ['pop' + c for c in conditions.keys() + ['']]:
            regwrite = ['sp']
            regread = ['sp']
            reglist = parseComSepList(args[0][1:-1])
            regwrite += reglist
        elif instr.getOpcode() in ['smull' + c for c in conditions.keys() + ['']]:
            regwrite = [args[0], args[1]]
            regread = [args[2], args[3]]
        elif instr.getOpcode() in ['mul' + c for c in conditions.keys() + ['']]:
            regwrite = [args[0]]
            regread = [args[1], args[2]]
        else:
            raise ValueError("Unknown instruction opcode: " + str(instr))

        return (regread, regwrite)
