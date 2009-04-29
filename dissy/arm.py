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


arm_calls = ['bl']
arm_conditionflag_setters = ['cmp', 'cmn', 'tst'] + \
    [i + "s" for i in
    ['asr', 'lsl', 'lsr', 'mla', 'mov', 'mul', 'mvn', 'ror', 'rrx', 'smlal',
     'smull', 'umlal', 'umull']
    ]
arm_conditionflag_users = ['']

arm_instr_descriptions = {
    'adc': 'Add with carry',
    'add': 'Add',
    'and': 'Logical and',
    'asr': 'Arithmetic Shift Right',
    'asrs': 'Arithmetic Shift Right and set condition flags',
    'bal': 'Unconditional Branch',
    'bic': 'Bit Clear',
    'blal': 'Unconditional Branch and Link',
    'bl': """Branch with Link
LR := Address of next instruction, PC := label""",
    'bx': """Branch and eXchange
PC := Rm""",
    'cmn': 'Compare (negative) two values and set condition flags',
    'cmp': 'Compare two values and set condition flags',
    'eor': 'Bitwise Exclusive OR',
    'eors': 'Bitwise Exclusive OR and set condition flags',
    'ldm': 'Load Multiple',
    'ldr': 'Load Register',
    'ldrb': 'Load Register Byte',
    'ldrh': 'Load Register Halfword',
    'ldrsh': 'Load Register Halfword and set condition flags',
    'lsl': 'Logical Shift Left',
    'lsls': 'Logical Shift Left and set condition flags',
    'lsr': 'Logical Shift Right',
    'lsrs': 'Logical Shift Right and set condition flags',
    'mla': 'Multiply and Accumulate',
    'mls': 'Multiply and Subtract',
    'mov': 'Move',
    'mul': 'Multiply',
    'muls': 'Multiply and set condition flags',
    'mvn': 'Move and negate (XOR 0xFFFFFFFF)',
    'orr': 'Bitwise OR',
    'orrs': 'Bitwise OR and set condition flags',
    'pop': """Pop from the stack.
Canonical form of "ldm SP!, <reglist>\"""",
    'push': """Push on the stack.
Canonical form of "stmdb SP!, <reglist>\"""",
    'rsb': 'Reverse Subtract',
    'rsbs': 'Reverse Subtract and set condition flags',
    'smull': """Signed Multiply Long
%(arg1)s,%(arg2)s := signed(%(arg3)s * %(arg4)s)""",
    'stm': 'Store Multiple',
    'str': 'Store Register',
    'strb': 'Store Register Byte',
    'strh': 'Store Register Halfword',
    'strsh': 'Store Register Halfword and set condition flags',
    'sub': 'Subtract',
    'tst': 'Test'
    }

arm_conditions = {
    'cc': 'Carry Clear',
    'cs': 'Carry Set',
    'eq': 'Equal (Zero Set)',
    'ge': 'Signed Greater than or Equal',
    'gt': 'Signed Greater Than',
    'hi': 'Unsigned Higher Than',
    'hs': 'Unsigned Higher or Same',
    'le': 'Signed Less than or Equal',
    'lo': 'Unsigned Lower Than',
    'ls': 'Unsigned Lower or Same',
    'lt': 'Signed Less Than',
    'mi': 'Minus (Negative)',
    'ne': 'Not Equal (Zero Clear)',
    'pl': 'Plus (Positive)',
    'vc': 'Overflow Clear',
    'vs': 'Overflow Set'
    }

arm_lists_inited = False
if not arm_lists_inited:
    conditional_instructions = {
        'add': """Add on %s""",
        'b': """Branch on %s
PC := label, label is this instruction +/-32Mb""",
        'bl': """Branch and Link on %s""",
        'bx': """Branch and eXchange on %s
PC := Rm
Change to Thumb mode if Rm[0] is 1, change to ARM mode if Rm[0] is 0""",
        'eor': """Bitwise Exclusive OR on %s""",
        'mov': """Move on %s""",
        'orr': """Bitwise OR on %s""",
        'sub': """Subtract on %s"""
        }

    for i in conditional_instructions:
        for c in arm_conditions:
            arm_instr_descriptions[i + c] = conditional_instructions[i] % (arm_conditions[c])
            arm_conditionflag_users += [i + c]
    arm_lists_inited = True

def crossproduct(s1, s2):
    ans = []
    for a in s1:
        for b in s2:
            ans += [a + b]
    return ans


arm_jumps = crossproduct(['b', 'bl'], arm_conditions.keys() + [''])

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
            * A list of the registers written to in this instruction
            * A list of the values used in this instruction"""

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
        def isValue(s):
            if s[:1] == '#':
	        if s[1:].isdigit():
                    return True
            return False
        regwrite = []
        regread = []
        values = []
        args = parseComSepList(instr.args)
        values = [int(a[1:]) for a in args if isValue(a)]

        if instr.getOpcode()[:3] in ['cmp', 'cmn', 'tst', 'teq']:
            regread = [a for a in args if isRegister(a)]
        elif instr.getOpcode()[:3] in ['add', 'and', 'asr', 'eor', 'lsl',
                                       'lsr', 'mov', 'mvn', 'orr', 'rsb',
                                       'sub']:
            regwrite = [args[0]]
            regread = [a for a in args[1:] if isRegister(a)]
        #branches
        elif instr.getOpcode() in crossproduct(['b'], arm_conditions.keys() + ['']):
            regwrite = ['pc']
        elif instr.getOpcode() in crossproduct(['bl'], arm_conditions.keys() + ['']):
            regwrite = ['pc', 'lr']
        elif instr.getOpcode() in crossproduct(['bx'], arm_conditions.keys() + ['']):
            regwrite = ['pc']
            regread = [args[0]]
        elif instr.getOpcode() in crossproduct(['blx'], arm_conditions.keys() + ['']):
            regwrite = ['pc']
            regread = isRegister(args[0]) and [args[0]] or []
        #load
        elif instr.getOpcode() in crossproduct(['ldr', 'ldrb', 'ldrh', 'ldrsh'], arm_conditions.keys() + ['']):
            regwrite = [args[0]]
            if args[1].startswith('['):
                offsetl = parseComSepList(args[1][1:-1])
                regread = [r for r in offsetl if isRegister(r)]
                values = [int(r[1:]) for r in offsetl if r[0] == '#']
        elif instr.getOpcode() in crossproduct(['ldm'], arm_conditions.keys() + ['']):
            regread = [args[0]]
            regwrite = parseComSepList(args[1][1:-1])
        #store
        elif instr.getOpcode() in crossproduct(['str', 'strb', 'strh', 'strsh'], arm_conditions.keys() + ['']):
            regread = [args[0]]
            if args[1].startswith('['):
                offsetl = parseComSepList(args[1][1:-1])
                regread += [r for r in offsetl if isRegister(r)]
        elif instr.getOpcode() in crossproduct(['stm'], arm_conditions.keys() + ['']):
            regread = [args[0]] + parseComSepList(args[1][1:-1])
        #push
        elif instr.getOpcode() in crossproduct(['push'], arm_conditions.keys() + ['']):
            regwrite = ['sp']
            regread = ['sp']
            reglist = parseComSepList(args[0][1:-1])
            regread += reglist
        elif instr.getOpcode() in crossproduct(['pop'], arm_conditions.keys() + ['']):
            regwrite = ['sp']
            regread = ['sp']
            reglist = parseComSepList(args[0][1:-1])
            regwrite += reglist
        elif instr.getOpcode() in crossproduct(['smull'], arm_conditions.keys() + ['']):
            regwrite = [args[0], args[1]]
            regread = [args[2], args[3]]
        elif instr.getOpcode() in crossproduct(['mla'], arm_conditions.keys() + ['']):
            regwrite = [args[0]]
            regread = args[1:]
        elif instr.getOpcode() in crossproduct(['mul', 'muls'], arm_conditions.keys() + ['']):
            regwrite = [args[0]]
            regread = [args[1], args[2]]
        elif instr.getOpcode() == '.word':
            return ([], [], [])
        else:
            raise ValueError("Unknown instruction opcode: " + str(instr))

        return (regread, regwrite, values)
