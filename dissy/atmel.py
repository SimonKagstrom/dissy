######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Mads Chr. Olesen <mchro@cs.aau.dk>
## Description:   ATMEL AVR 8-bit arch specific stuff
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import sys, architecture
from dissy.architecture import Architecture


atmel_calls = ['rcall', 'icall', 'call', 'eicall']
atmel_conditionflag_setters = ['cp', 'cpi', 'cpc']
atmel_conditionflag_users = ['']

atmel_instr_descriptions = {
    'ld': """Load Indirect
Note that:
X = r26:r27
Y = r28:r29
Z = r30:r31""",
    'ldi': 'Load Immediate',
    'ldd': """Load Indirect with Displacement
Note that:
X = r26:r27
Y = r28:r29
Z = r30:r31""",
    'lds': 'Load Indirect from Data Space',

    'st': """Store Indirect
Note that:
X = r26:r27
Y = r28:r29
Z = r30:r31""",
    'std': """Store Indirect with Displacement
Note that:
X = r26:r27
Y = r28:r29
Z = r30:r31""",
    'sts': 'Store Direct to Data Space',

    'in': """In from I/O Location

Note that:
0x3d = Stack pointer low byte
0x3e = Stack pointer high byte""",
    'out': """Out to I/O Location

Note that:
0x3d = Stack pointer low byte
0x3e = Stack pointer high byte
0x3f = Status register accumulator""",
    'rcall': """Relative Call Subroutine

Note on <tt>rcall .+0</tt>: this is sometimes used to atomically decrement the stack pointer, \
in order to allocate space on the stack for later use.""",
    'ret': 'Subroutine return',
    'rjmp': 'Relative Jump',
    'sbrc': 'Skip if Bit in Register Cleared',
    'sbrs': 'Skip if Bit in Register Set',

    'add': 'Add without Carry',
    'adc': 'Add with Carry',
    'adiw': """Add Immediate to Word
Only possible for the register pairs:
    r24:r25
X = r26:r27
Y = r28:r29
Z = r30:r31""",
    'inc': 'Increment',

    'sub': 'Subtract without Carry',
    'sbc': 'Subtract with Carry',
    'subi': 'Subtract Immediate',
    'sbci': 'Subtract Immediate with Carry',
    'sbiw': """Subtract Immediate from Word
Only possible for the register pairs:
    r24:r25
X = r26:r27
Y = r28:r29
Z = r30:r31""",
    'dec': 'Decrement',

    'lsl': 'Logical Shift Left',
    'lsr': 'Logical Shift Right',
    'rol': 'Rotate Left Through Carry',
    'ror': 'Rotate Right Through Carry',
    'asr': 'Arithmetic Shift Right',

    'and': 'Logical AND',
    'andi': 'Logical AND with Immediate',
    'or': 'Logical OR',
    'ori': 'Logical ORwith Immediate',
    'eor': 'Exclusive OR',
    'com': 'One\'s Complement',
    'neg': 'Two\'s Complement',

    'cp': 'Compare',
    'cpc': """Compare with Carry
Compares two registers, also taking the previously set carry bit into account.""",
    'cpi': 'Compare with Immediate',

    'mov': 'Copy Register',
    'swap': 'Swap Nibbles',
    'bst': 'Bit Store from Register to T',
    'bld': 'Bit Load from T to Register',

    'push': 'Push Register on Stack',
    'pop': 'Pop Register from Stack',

    'sec': 'Set Carry',

    'cli': 'Global Interrupt Disable',
    }

atmel_conditions = {
    'eq': 'Equal',
    'ne': 'Not Equal',
    'ge': 'Greater or Equal, Signed',
    'lt': 'Less Than, Signed',
    'pl': 'Positive (Plus)',
    'mi': 'Negative (Minus)',
    'tc': 'T Flag Cleared',
    'ts': 'T Flag Set',
    'cs': 'Carry Set',
    'cc': 'Carry Cleared',
    }

def crossproduct(s1, s2):
    ans = []
    for a in s1:
        for b in s2:
            ans += [a + b]
    return ans

atmel_lists_inited = False
if not atmel_lists_inited:
    conditional_instructions = {
        'br': """Branch if %s
PC := PC + k + 2""",
        }

    for i in conditional_instructions:
        for c in atmel_conditions:
            atmel_instr_descriptions[i + c] = conditional_instructions[i] % (atmel_conditions[c])
            atmel_conditionflag_users += [i + c]
    atmel_lists_inited = True

atmel_jumps = ['rjmp', 'jmp'] + list(crossproduct(['br'], atmel_conditions.keys())) + \
    atmel_calls + ['sbrc', 'sbrs', 'sbic', 'sbis']

atmel_branches = list(crossproduct(['br'], atmel_conditions.keys()) + \
    ['sbrc', 'sbrs', 'sbic', 'sbis'])

class AtmelArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, atmel_jumps, atmel_calls,
            atmel_conditionflag_setters, atmel_conditionflag_users)

    def getJumpDestination(self, address, insn, args):
        #example:
        #address = 84L
        #insn = 'brge'
        #args = '.+6     '

        if insn in ['sbrc', 'sbrs']: #skip instructions
            #TODO XXX: this depends on the size of the instruction skipped!
            # (can be 16 or 32 bits (jmp, call, lds, sts))
            return long(address + 4)
        if args[0] == '.': #relative jump
            offset = long(args[1:])
            return long(address + offset + 2)
        else: #absolute jump?
            return Architecture.getJumpDestination(self, address, insn, args)

    def getInstructionInfo(self, instruction):
        opcode = instruction.opcode
        args = str(instruction.getArgs())

        args_list = args.split(", ")
        args_dict = dict(
            zip(['arg' + str(i) for i in range(1, len(args_list)+1)],
                args_list))
        description = atmel_instr_descriptions.get(instruction.opcode, '')

        return {'shortinfo': opcode + " " + args,
                'description': description % args_dict,
                }

    def isReturn(self, insn):
        if insn.opcode == 'ret':
            return True
        return False

    def isBranch(self, insn):
        """Returns true if this instruction is a branch, that is it can either
        be taken or not be taken."""
        return insn.opcode in atmel_branches

    parseArguments_opcodelook = {}
    def parseArguments(self, instr):
        """Parses an argument string, into a tuple, containing:
            * A list of the registers read in this instruction
            * A list of the registers written to in this instruction
            * A list of the values used in this instruction"""
        #XXX
        return ([], [], [])

    def getInstructionEffect(self, ins, func):
        """
        Returns a string describing the effects on the registers, of this
        instruction. An example of such a string is:
        "r1 = 5 ; r2 = r3 + r4 ; r7 = top"

        Used for the value analysis.
        """
        #XXX
        return ""

    def getInstructionStackEffect(self, ins, func):
        #XXX, can only push/pop one reg.
        opc = ins.opcode
        if opc == 'push':
            (regsread, regswrite, values) = self.parseArguments(ins)
            return "push " + " ; ".join([self.normalize_regname(a) for a in regsread if a != 'sp'])
        elif opc == 'pop':
            (regsread, regswrite, values) = self.parseArguments(ins)
            regstopop = [self.normalize_regname(a) for a in regswrite if a != 'sp']
            regstopop.reverse()
            return "pop " + " ; ".join(regstopop)
        return ""

    def get_ins_type(self, opcode):
        """
        Returns the type of instruction.
        One of: XXX TODO
        """
        if opcode in ['sts', 'st', 'std']:
            return 'INSTR_STORE'
        elif opcode in ['lds', 'ld', 'ldd']:
            return 'INSTR_LOAD'
        elif opcode == 'push':
            return 'INSTR_PUSH'
        elif opcode == 'pop':
            return 'INSTR_POP'
        #"common" instructions
        elif opcode in ['add', 'adc', 'sub', 'subi', 'sbc', 'sbci', 'and', 'andi', 'or',
            'ori', 'eor', 'com', 'neg', 'sbr', 'cbr', 'inc', 'dec', 'tst', 'clr', 'ser',
            'cp', 'cpc', 'cpi',
            'mov', 'movw', 'ldi', 'lsl', 'lsr', 'rol', 'ror', 'asr', 'swap', 'sbi', 'cbi',
            'sec', 'bst', 'bld', 'cli', 'in', 'out']:
            return "INSTR_OTHER"
        elif opcode in ['sbiw', 'adiw', 'mul', 'muls', 'mulsu', 'fmul', 'fmuls', 'fmulsu']:
            return "INSTR_WORD_ARITH"
        #branches to static locations
        elif opcode in ['rjmp']:
            return "INSTR_JUMP"
        elif opcode in list(crossproduct(['br'], atmel_conditions.keys())) + \
            ['sbrc', 'sbrs', 'sbic', 'sbis']:
            return "INSTR_BRANCH"
        elif opcode in ['rcall']:
            return "INSTR_RCALL"
        elif opcode in ['call']:
            return "INSTR_CALL"
        elif opcode in ['ret']:
            return "INSTR_RET"
        else:
            print "Unhandled opcode '" + opcode + "'"
            return "INSTR_OTHER"

    def normalize_regname(self, regname):
        #XXX
        return regname

    def denormalize_regname(self, regname):
        #XXX
        return regname
