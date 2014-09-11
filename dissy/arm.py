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
Canonical form of "ldm SP!, &lt;reglist&gt;\"""",
    'push': """Push on the stack.
Canonical form of "stmdb SP!, &lt;reglist&gt;\"""",
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



arm_jumps = list(crossproduct(['b', 'bl'], arm_conditions.keys() + ['']))

arm_branches = list(crossproduct(['b', 'bl'], arm_conditions.keys()))

class ArmArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, arm_jumps, arm_calls,
            arm_conditionflag_setters, arm_conditionflag_users)

    def getInstructionInfo(self, instruction):
        opcode = instruction.opcode
        args = str(instruction.getArgs())

        args_list = args.split(", ")
        args_dict = dict(
            zip(['arg' + str(i) for i in range(1, len(args_list)+1)],
                args_list))
        description = arm_instr_descriptions.get(instruction.opcode, '')

        return {'shortinfo': opcode + " " + args,
                'description': description % args_dict,
                }

    def isReturn(self, insn):
        if insn.opcode == 'bx' and insn.getArgs() == 'lr':
            return True
        return False

    def isBranch(self, insn):
        """Returns true if this instruction is a branch, that is it can either
        be taken or not be taken."""
        return insn.opcode in arm_branches

    parseArguments_opcodelook = {}
    def parseArguments(self, instr):
        """Parses an argument string, into a tuple, containing:
            * A list of the registers read in this instruction
            * A list of the registers written to in this instruction
            * A list of the values used in this instruction"""

        def parseComSepList(lstr):
            if not '[' in lstr and not '{' in lstr:
                return lstr.replace(' ', '').split(',')
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
                    if tmp != '':
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
            if s != "" and s[0] == 'r' and s[1:].isdigit(): #r0..r15
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
            if s != "" and s[0] == '#' and s[1:].isdigit():
                return True
            return False
        regwrite = []
        regread = []
        values = []
        args = parseComSepList(instr.args)
        values = [int(a[1:]) for a in args if isValue(a)]

        #Lazy init
        if not self.parseArguments_opcodelook:
            for opcode in crossproduct(['b'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'b'
            for opcode in crossproduct(['bl'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'bl'
            for opcode in crossproduct(['bx'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'bx'
            for opcode in crossproduct(['blx'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'blx'
            for opcode in crossproduct(['ldr', 'ldrb', 'ldrh', 'ldrsh'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'ldr'
            for opcode in crossproduct(['ldm'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'ldm'
            for opcode in crossproduct(['str', 'strb', 'strh', 'strsh'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'str'
            for opcode in crossproduct(['stm'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'stm'
            for opcode in crossproduct(['push'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'push'
            for opcode in crossproduct(['pop'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'pop'
            for opcode in crossproduct(['stmia', 'stmib', 'stmda', 'stmdb'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'stm_nonstandard'
            for opcode in crossproduct(['ldmia', 'ldmib', 'ldmda', 'ldmdb'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'ldm_nonstandard'
            for opcode in crossproduct(['smull'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'smull'
            for opcode in crossproduct(['mla'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'mla'
            for opcode in crossproduct(['mul', 'muls'], arm_conditions.keys() + ['']):
                self.parseArguments_opcodelook[opcode] = 'mul'

        opcode = instr.opcode
        opcodetype = self.parseArguments_opcodelook.get(opcode, opcode)
        if opcode[:3] in ['cmp', 'cmn', 'tst', 'teq']:
            regread = [a for a in args if isRegister(a)]
        elif opcode[:3] in ['add', 'and', 'asr', 'eor', 'lsl',
                                       'lsr', 'mov', 'mvn', 'orr', 'rsb',
                                       'sub']:
            regwrite = [args[0]]
            regread = [a for a in args[1:] if isRegister(a)]
        #branches
        elif opcodetype == 'b':
            regwrite = ['pc']
        elif opcodetype == 'bl':
            regwrite = ['pc', 'lr']
        elif opcodetype == 'bx':
            regwrite = ['pc']
            regread = [args[0]]
        elif opcodetype == 'blx':
            regwrite = ['pc']
            regread = isRegister(args[0]) and [args[0]] or []
        #load
        elif opcodetype == 'ldr':
            regwrite = [args[0]]
            if args[1].startswith('['):
                offsetl = parseComSepList(args[1][1:-1])
                regread = [r for r in offsetl if isRegister(r)]
                values = [int(r[1:]) for r in offsetl if r[0] == '#']
        elif opcodetype == 'ldm':
            regread = [args[0]]
            regwrite = parseComSepList(args[1][1:-1])
        #store
        elif opcodetype == 'str':
            regread = [args[0]]
            if args[1].startswith('['):
                offsetl = parseComSepList(args[1][1:-1])
                regread += [r for r in offsetl if isRegister(r)]
            #postindexing
            if len(args) == 3:
                regwrite += [regread[1]]
                if isRegister(args[2]):
                    regread += [args[2]]
        elif opcodetype == 'stm':
            regread = [args[0]] + parseComSepList(args[1][1:-1])
        #push
        elif opcodetype == 'push':
            regwrite = ['sp']
            regread = ['sp']
            reglist = parseComSepList(args[0][1:-1])
            regread += reglist
        #pop
        elif opcodetype == 'pop':
            regwrite = ['sp']
            regread = ['sp']
            reglist = parseComSepList(args[0][1:-1])
            regwrite += reglist
        #store multiple
        elif opcodetype == 'stm_nonstandard':
            regwrite = [args[0]]
            regread = [args[0]]
            reglist = parseComSepList(args[1][1:-1])
            regread += reglist
        #load multiple
        elif opcodetype == 'ldm_nonstandard':
            regwrite = [args[0]]
            regread = [args[0]]
            reglist = parseComSepList(args[1][1:-1])
            regwrite += reglist
        elif opcodetype == 'smull':
            regwrite = [args[0], args[1]]
            regread = [args[2], args[3]]
        elif opcodetype == 'mla':
            regwrite = [args[0]]
            regread = args[1:]
        elif opcodetype == 'mul':
            regwrite = [args[0]]
            regread = [args[1], args[2]]
        elif opcode == '.word':
            return ([], [], [])
        else:
            raise ValueError("Unknown instruction opcode: " + str(instr))

        return (regread, regwrite, values)

    def getInstructionEffect(self, ins, func):
        """
        Returns a string describing the effects on the registers, of this
        instruction. An example of such a string is:
        "r1 = 5 ; r2 = r3 + r4 ; r7 = top"

        Used for the value analysis.
        """
        opc = ins.opcode
        (regsread, regswrite, values) = self.parseArguments(ins)

        if opc == "ldr":
            #PC relative load
            if regsread == ['pc'] and len(values) == 1:
                #Calculate address (+8 to account for pipeline)
                addr = ins.address + 8 + values[0]
                #Find data
                data = func.lookup(addr)
                assert data.opcode == '.word'
                return self.normalize_regname(regswrite[0]) + "=" + str(int(data.getArgs(), 16))
                #print func.getAll()
        elif opc in ['mov', 'movs']:
            #mov rX, value
            if len(regswrite) == 1 and regsread == [] and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + str(values[0]) 
            #mov rX, rY
            elif len(regswrite) == 1 and len(regsread) == 1 and len(values) == 0:
                return self.normalize_regname(regswrite[0]) + "=" + self.normalize_regname(regsread[0]) 
        elif opc in ['add', 'adds']:
            #add rX, rY, value
            if len(regswrite) == 1 and len(regsread) == 1 and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[0]) + " + " + str(values[0])
            #add rX, rY, rZ
            elif len(regswrite) == 1 and len(regsread) == 2 and len(values) == 0:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[0]) + " + " + \
                    self.normalize_regname(regsread[1])
        elif opc in ['sub', 'subs']:
            #sub rX, rY, value
            if len(regswrite) == 1 and len(regsread) == 1 and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[0]) + " - " + str(values[0])
            #sub rX, rY, rZ
            elif len(regswrite) == 1 and len(regsread) == 2 and len(values) == 0:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[0]) + " - " + \
                    self.normalize_regname(regsread[1])
        elif opc == 'rsb':
            #rsb rX, rY, value   (rX = value - rY)
            if len(regswrite) == 1 and len(regsread) == 1 and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    str(values[0]) + " - " + self.normalize_regname(regsread[0])
            #rsb rX, rY, rZ
            elif len(regswrite) == 1 and len(regsread) == 2 and len(values) == 0:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[1]) + " - " + \
                    self.normalize_regname(regsread[0])
        elif opc == 'lsl':
            #TODO XXX - is this totally correct? See 
            #http://en.wikipedia.org/wiki/Arithmetic_shift and
            #http://en.wikipedia.org/wiki/Logical_shift

            #lsl rX, rY, value
            if len(regswrite) == 1 and len(regsread) == 1 and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[0]) + " << " + str(values[0])
        elif opc == 'asr':
            #asr rX, rY, value
            if len(regswrite) == 1 and len(regsread) == 1 and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regsread[0]) + " >> " + str(values[0])
        elif opc == 'push':
            dataregs = [a for a in regsread if a != 'sp']
            return self.normalize_regname('sp') + " = " + self.normalize_regname('sp') + " - " + \
                str(len(dataregs) * 4)
        elif opc == 'pop':
            dataregs = [a for a in regswrite if a != 'sp']
            return "".join(map(lambda x: self.normalize_regname(x) + " = top ; ", dataregs))+ \
                self.normalize_regname('sp') + " = " + self.normalize_regname('sp') + " + " + \
                str(len(dataregs) * 4)
        #store with postindexing
        elif opc == 'str' and len(regswrite) == 1:
            #register offset
            if len(regsread) == 3 and len(values) == 0:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regswrite[0]) + " + " + self.normalize_regname(regsread[2])
            #immediate offset
            if len(regsread) == 2 and len(values) == 1:
                return self.normalize_regname(regswrite[0]) + "=" + \
                    self.normalize_regname(regswrite[0]) + " + " + str(values[0])
        
        #unknown effect
        if len(regswrite) > 0:
            return "".join(map(lambda x: self.normalize_regname(x) + " = top ; ", regswrite))

        #No effect
        return ""

    def getInstructionStackEffect(self, ins, func):
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
        #XXX - this can be optimized _greatly_ by lazy initing the crossproducts,
        #instead of constructing them each time.
        if opcode in crossproduct(['stm', 'stmda', 'stmdb', 'stmia', 'stmib',
                                   'str', 'strb', 'strh', 'strsh'],
                                  arm_conditions.keys() + ['']):
            return 'INSTR_STORE'
        elif opcode in crossproduct(['ldm', 'ldmda', 'ldmdb', 'ldmia', 'ldmib',
                                     'ldr', 'ldreq', 'ldrls'],
                                    arm_conditions.keys() + ['']):
            return 'INSTR_LOAD'
        elif opcode in crossproduct(['ldrb', 'ldrh', 'ldrsh'],
                                    arm_conditions.keys() + ['']):
            return 'INSTR_LOADROTATE'
        elif opcode == 'push':
            return 'INSTR_PUSH'
        elif opcode == 'pop':
            return 'INSTR_POP'
        #"common" instructions
        elif opcode in crossproduct(['add', 'adds', 'and', 'asr', 'asrs', 'cmn',
                                     'cmp', 'eor', 'eors', 'lsl', 'lsls', 'lsr',
                                     'lsrs', 'mov', 'mvn', 'orr', 'orrs', 'rsb',
                                     'rsbs', 'sub', 'subs', 'tst', 'movs', 'teq'],
                                     arm_conditions.keys() + ['']):
            return "INSTR_OTHER"
        elif opcode in crossproduct(['mul', 'mla', 'muls'],
                                    arm_conditions.keys() + ['']):
            return "INSTR_MUL1"
        elif opcode in crossproduct(['smull', 'umull', 'smlal', 'umlal'],
                                    arm_conditions.keys() + ['']):
            return "INSTR_MUL2"
        #branches to static locations
        elif opcode in crossproduct(['b', 'bl', 'bx'], arm_conditions.keys() + ['']):
            return "INSTR_OTHER"
        else:
            #print "Unhandled opcode '" + opcode + "'"
            return "INSTR_OTHER"

    def normalize_regname(self, regname):
        return {'sl': 'r10', 
                'fp': 'r11', 
                'ip': 'r12', 
                'sp': 'r13',
                'lr': 'r14',
                #'pc': 'r15'
                }.get(regname, regname)

    def denormalize_regname(self, regname):
        return {'r10': 'sl', 
                'r11': 'fp', 
                'r12': 'ip', 
                'r13': 'sp',
                'r14': 'lr',
                #'r15': 'pc'
                }.get(regname, regname)
