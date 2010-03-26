######################################################################
##
## Copyright (C) 2009,  Mads Chr. Olesen
##
## Author:        Mads Chr. Olesen <mads@mchro.dk>
## Description:   Value analysis
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################

import sys
import re
import wali
import dissy.File
from dissy.Function import Function
from dissy.Instruction import Instruction
from dissy.arm import ArmArchitecture
from dissy.constdom import ConstDom

#The initial python environment to evaluate expressions in
initial_env = {}

def all_loopbound_combinations(max_loopbounds):
    if len(max_loopbounds) == 0:
        yield ()
    elif len(max_loopbounds) == 1:
        for i in range(0, max_loopbounds[0]):
            yield (i, )
    else:
        for i in range(0, max_loopbounds[0]):
            for j in all_loopbound_combinations(max_loopbounds[1:]):
                yield tuple([i] + list(j))

find_loop_bound_re = re.compile('@loop_bound\ ([0-9]+)')
def find_loop_bound(s):
    l = find_loop_bound_re.findall(s)
    if len(l) > 0:
        return l[len(l)-1]
    else:
        return None

#TODO, these should probably be arch-dependent
library_function_loopbounds = {
    #ARM functions
    #TODO XXX - I have _NO_ idea if these bounds are correct - mchro
    '__divsi3': {
        0x50: 5,
        0x64: 5,
        0xa8: 5,
    },
    #TODO XXX - I have _NO_ idea if these bounds are correct - mchro
    '__udivsi3': {
        0x3c: 5,
        0x50: 5,
        0x94: 5,
    },
    '__aeabi_uidivmod': { },

    #ATMEL AVR 8-bit functions
    '_div': { 0x1c: 1 },
    #these bounds should be correct - mchro
    '__mulsi3': { },
    '__mulhi3': { 0x1c: 16 },
    '__udivmodhi4': { 0x1c: 16 },
    '__divmodsi4': { 0x24: 1 },
    '__divmodsi4_neg1': { 0x0: 0 },
    '__divmodsi4_neg2': { },
    #argh, this branch moves around alot...
    '__udivmodsi4': { 0x30: 32, 0x32: 32},
}
handled_library_functions = library_function_loopbounds.keys()

def find_loopbounds(func):
    loop_bounds = {}

    #Is library function?
    if func.getLabel() in library_function_loopbounds:
        library_loop_bounds = library_function_loopbounds[func.getLabel()]
        for i in library_loop_bounds:
            loop_bounds[func.address + i] = library_loop_bounds[i]
        return loop_bounds
    
    #find loop bounds
    last_loop_bound = 'NO_LOOP_BOUND'
    for line in func.getAll():
        if isinstance(line, Instruction):
            other = line.outLink
            if isinstance(other, Instruction) and other != line:
                if other.address < line.address: # BACKWARDS jump
                    #get loop bound from comment, if applicable
                    last_loop_bound = find_loop_bound(line.comment) or last_loop_bound
                    if last_loop_bound != 'NO_LOOP_BOUND':
                        loop_bounds[line.address] = int(last_loop_bound)
                        if line.comment == '':
                            line.comment = "@loop_bound %s" % last_loop_bound
                    else:
                        loop_bounds[line.address] = last_loop_bound
                        if line.comment == '':
                            line.comment = "@loop_bound NO_LOOP_BOUND (not handled)"
        else:
            last_loop_bound = find_loop_bound(str(line)) and \
                find_loop_bound(str(line)) or last_loop_bound

    #print "Loop bounds: {",
    #for k in loop_bounds.keys():
    #    print hex(k), ":", loop_bounds[k], ",",
    #print "}"

    return loop_bounds


def crossproduct(s1, s2):
    ans = []
    for a in s1:
        for b in s2:
            ans += [a + b]
    return ans

def getNoEffect():
    return wali.SemElemPtr( ConstDom("") )

def getZeroElement():
    return getNoEffect().zero()

def loopcontext_to_str(cur_loopbounds):
    branch_addrs = cur_loopbounds.keys()
    branch_addrs.sort()
    branch_addrs.reverse()
    lbs = []
    for i in branch_addrs:
        lbs += [cur_loopbounds[i]]
        
    return "_".join(map(str, lbs))

loopcontexts_seen = {}
def construct_wpds(f):
    global loopcontexts_seen
    arch = f.getArch()
    wpds = wali.WPDS()
    #the state of our automaton
    p = wali.getKey("p")

    #Helper function, to wrap into the WALi framework, and cache effects
    instructionEffectCache = {}
    def getInstructionEffect(ins, func):
        if (ins, func) in instructionEffectCache:
            return instructionEffectCache[(ins, func)]
        else:
            effect = wali.SemElemPtr( 
                ConstDom( 
                    arch.getInstructionEffect(ins, func), 
                    arch.getInstructionStackEffect(ins, func) 
                ) )
            instructionEffectCache[(ins, func)] = effect
            return effect

    for func in f.getFunctions():
        instructions = func.getInstructions()
        if func.getLabel()[0:2] != '__':

            loop_bounds = find_loopbounds(func)
            
            #Copy loopbounds
            cur_loopbounds = dict(loop_bounds)
            for i in cur_loopbounds:
                cur_loopbounds[i] = 0
            loopcontexts_seen[func.getLabel()] = [dict(cur_loopbounds)]

            #Function start transition
            ins = instructions[0]
            k0 = wali.getKey("f_" + func.getLabel())
            k1 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                loopcontext_to_str(cur_loopbounds))
            effect = getNoEffect()
            wpds.add_rule(p, k0, p, k1, effect)

            i = 0
            indentlevel = -1

            while i < len(instructions):
                ins = instructions[i]
                #print i, ins

                #unconditional branch ("Function call")
                if isinstance(ins.getOutLink(), Function): #TODO check that jump is unconditional
                    k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                        loopcontext_to_str(cur_loopbounds))
                    k1 = wali.getKey("f_" + ins.getOutLink().getLabel())
                    effect = getInstructionEffect(ins, func)

                    #Special case: Function call as last instruction, no return from this call - handle as sort of sequential
                    #if len(instructions) - 1 == i:
                    if ins.opcode == 'b':
                        wpds.add_rule(p, k0, p, k1, effect)
                        i += 1
                    else:
                        nextins = instructions[i+1]
                        i += 1

                        k2 = wali.getKey(hex(nextins.address)[:-1] + "_" + \
                            loopcontext_to_str(cur_loopbounds))
                        wpds.add_rule(p, k0, p, k1, k2, effect)
                    continue
                #jump
                #TODO arch specific to ARM
                elif isinstance(ins.getOutLink(), Instruction) and \
                    not ins.getOpcode() in ['bl', 'bx'] and \
                    len(ins.getOpcode()) > 1:

                    #Forward jump
                    if ins.getOutLink().address > ins.address:
                        #Jump taken
                        nextins = ins.getOutLink()
                        k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                            loopcontext_to_str(cur_loopbounds))
                        k1 = wali.getKey(hex(nextins.address)[:-1] + "_" + \
                            loopcontext_to_str(cur_loopbounds))
                        effect = getInstructionEffect(ins, func)
                        wpds.add_rule(p, k0, p, k1, effect)

                        #TODO arch specific to ARM
                        if len(ins.getOpcode()) > 1: #Conditional jump, possibility of sequential
                            nextins = instructions[i+1]
                            k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                                loopcontext_to_str(cur_loopbounds))
                            k1 = wali.getKey(hex(nextins.address)[:-1] + "_" + \
                                loopcontext_to_str(cur_loopbounds))
                            effect = getInstructionEffect(ins, func)
                            wpds.add_rule(p, k0, p, k1, effect)

                        i += 1
                        continue
                    #Backward jump
                    elif ins.getOutLink().address < ins.address:
                        #examine loopbound, to find out if we unroll,
                        if cur_loopbounds[ins.address] < loop_bounds[ins.address]-1:
                            if cur_loopbounds[ins.address] == 0:
                                indentlevel += 1
                            #print '  ' * indentlevel + 'Unrolling loop at', hex(ins.address)[:-1],
                            #print cur_loopbounds[ins.address], "/", loop_bounds[ins.address]

                            #keep unrolling, take loop edge
                            nextins = ins.getOutLink()
                            i = instructions.index(nextins)
            
                            k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                                loopcontext_to_str(cur_loopbounds))

                            cur_loopbounds[ins.address] += 1
                            loopcontexts_seen[func.getLabel()] += [dict(cur_loopbounds)]

                            k1 = wali.getKey(hex(nextins.address)[:-1] + "_" + \
                                loopcontext_to_str(cur_loopbounds))
                            effect = getInstructionEffect(ins, func)
                            wpds.add_rule(p, k0, p, k1, effect)

                            continue
                        else:
                            #loopbound reached, go on sequentially
                            nextins = instructions[i+1]
                            i += 1

                            k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                                loopcontext_to_str(cur_loopbounds))

                            #reset loop counter
                            cur_loopbounds[ins.address] = 0
                            loopcontexts_seen[func.getLabel()] += [dict(cur_loopbounds)]

                            k1 = wali.getKey(hex(nextins.address)[:-1] + "_" + \
                                loopcontext_to_str(cur_loopbounds))
                            effect = getInstructionEffect(ins, func)
                            wpds.add_rule(p, k0, p, k1, effect)
                            indentlevel -= 1
                            continue
                    else:
                        assert (False) #Jump to self is crazy

                #"Return"
                elif ins.getOpcode() == 'bx' and ins.getArgs() == 'lr': #TODO arch specific to ARM
                    k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                        loopcontext_to_str(cur_loopbounds))
                    
                    effect = getInstructionEffect(ins, func)
                    wpds.add_rule(p, k0, p, effect)

                    i += 1
                    continue
                #Sequential progression
                elif i < len(instructions)-1:
                    nextins = instructions[i+1]
                    i += 1
                else:
                    i += 1
                    continue

                k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                    loopcontext_to_str(cur_loopbounds))
                k1 = wali.getKey(hex(nextins.address)[:-1] + "_" + \
                    loopcontext_to_str(cur_loopbounds))
                effect = getInstructionEffect(ins, func)
                wpds.add_rule(p, k0, p, k1, effect)
    return wpds


def calculate_calling_contexts_test(f, answer):
    """Calculates the combined calling context for each function
    @returns dict from function names -> calling context as SemElem"""

    #the state of our automaton
    p = wali.getKey("p")

    toret = {}
    #Traverse the CFG, from main, looking for function calls
    mainfunc = [func for func in f.getFunctions() if func.getLabel() == 'main'][0]
    toret[mainfunc.getLabel()] = getNoEffect()
    funcqueue = [mainfunc]

    while len(funcqueue) > 0:
        func = funcqueue.pop()
        instructions = func.getInstructions()

        if func.getLabel()[0:2] != '__':

            loop_bounds = find_loopbounds(func)
            
            #Copy loopbounds
            cur_loopbounds = dict(loop_bounds)
            for i in cur_loopbounds:
                cur_loopbounds[i] = 0

            i = 0
            indentlevel = -1

            while i < len(instructions):
                ins = instructions[i]

                #unconditional branch ("Function call")
                if isinstance(ins.getOutLink(), Function): #TODO check that jump is unconditional
                    print 'now at', hex(ins.address)
                    f2 = ins.getOutLink()
                    
                    curcontext = toret.get(f2.getLabel(), None)
                    #print "got", curcontext

                    #print 'lb', lb
                    k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                        "_".join( map(str, cur_loopbounds) ))

                    transitions = answer.match(p, k0).asList()
                    assert(len(transitions) in [0,1])
                    #If reachable in this loop context
                    if len(transitions) == 1:
                        trans = transitions[0]
                        #print "extending", toret.get(func.getLabel()),  "with", trans.weight()
                        thiscontext = toret.get(func.getLabel()).extend(trans.weight())
                        print "combining", curcontext, "and", thiscontext
                        if curcontext is None:
                            curcontext = thiscontext
                        else:
                            curcontext = curcontext.combine(thiscontext)
                        #print "combine result", curcontext

                    toret[f2.getLabel()] = curcontext
                    funcqueue += [ins.getOutLink()]

                    #Special case: Function call as last instruction, no return from this call - handle as sort of sequential
                    if len(instructions) - 1 == i:
                        i += 1
                    else:
                        nextins = instructions[i+1]
                        i += 1
                    continue
                elif isinstance(ins.getOutLink(), Instruction) and \
                    not ins.getOpcode() in ['bl', 'bx'] and \
                    len(ins.getOpcode()) > 1:
                    #Forward jump
                    if ins.getOutLink().address > ins.address:
                        i += 1
                        continue
                    #Backward jump
                    elif ins.getOutLink().address < ins.address:
                        #examine loopbound, to find out if we unroll,
                        if cur_loopbounds[ins.address] < loop_bounds[ins.address]-1:
                            if cur_loopbounds[ins.address] == 0:
                                indentlevel += 1
                            #print '  ' * indentlevel + 'Unrolling loop at', hex(ins.address)[:-1],
                            #print cur_loopbounds[ins.address], "/", loop_bounds[ins.address]

                            #keep unrolling, take loop edge
                            nextins = ins.getOutLink()
                            i = instructions.index(nextins)
            
                            cur_loopbounds[ins.address] += 1
                            continue
                        else:
                            #loopbound reached, go on sequentially
                            nextins = instructions[i+1]
                            i += 1

                            #reset loop counter
                            cur_loopbounds[ins.address] = 0

                            indentlevel -= 1
                            continue

                #"Return"
                elif ins.getOpcode() == 'bx' and ins.getArgs() == 'lr': #TODO arch specific to ARM
                    i += 1
                    continue
                #Sequential progression
                elif i < len(instructions)-1:
                    nextins = instructions[i+1]
                    i += 1
                else:
                    i += 1
                    continue




def calculate_calling_contexts(f, answer):
    """Calculates the combined calling context for each function
    @returns dict from function names -> calling context as SemElem"""

    #the state of our automaton
    p = wali.getKey("p")

    toret = {}
    #Traverse the CFG, from main, looking for function calls
    mainfunc = [func for func in f.getFunctions() if func.getLabel() == 'main'][0]
    toret[mainfunc.getLabel()] = getNoEffect()
    funcqueue = [mainfunc]

    while len(funcqueue) > 0:
        func = funcqueue.pop()
        
        #XXX
        #k0 = wali.getKey("f_" + func.getLabel())
        #transitions = answer.match(p, k0).asList()
        #print len(transitions)
        #print transitions[0].weight()
        #import pdb; pdb.set_trace()

        #loop_bounds = find_loopbounds(func)
        
        print 'traversing func', func.getLabel()
        for ins in func.getInstructions():
            if isinstance(ins.getOutLink(), Function):
                print 'now at', hex(ins.address)
                #import pdb; pdb.set_trace()
                f2 = ins.getOutLink()
                
                curcontext = toret.get(f2.getLabel(), None)
                #print "got", curcontext

                #traverse the different loopbound contexts
                #print loopcontexts_seen[func.getLabel()]
                #for lb in all_loopbound_combinations(loop_bounds.values()):
                for lb in loopcontexts_seen[func.getLabel()]:
                    #print 'lb', lb.values()
                    k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                        "_".join( map(str, lb.values()) ))

                    transitions = answer.match(p, k0).asList()
                    if not len(transitions) in [0,1]:
                        import pdb; pdb.set_trace()
                    assert(len(transitions) in [0,1])
                    #If reachable in this loop context
                    if len(transitions) == 1:
                        trans = transitions[0]
                        #print "extending", toret.get(func.getLabel()),  "with", trans.weight()
                        #if toret.get(func.getLabel()) is None:
                        #    import pdb; pdb.set_trace()
                        thiscontext = toret.get(func.getLabel()).extend(trans.weight())
                        #print "combining", curcontext, "and", thiscontext
                        if curcontext is None:
                            curcontext = thiscontext
                        else:
                            curcontext = curcontext.combine(thiscontext)
                        #print "combine result", curcontext

                #if curcontext is None:
                #    import pdb; pdb.set_trace()
                toret[f2.getLabel()] = curcontext
                #dont calculate calling contexts for things called by library funcs
                if f2.getLabel()[:2] != '__':
                    funcqueue += [ins.getOutLink()]

    return toret

def regval_from_value_exprs(value_exprs, reg):
    """
    @param value_exprs is a dict from regname -> expression
    @param reg is the regname to compute the value of
    """
    #find value of register
    #regname = normalize_regname(reg)
    regname = reg
    val = evaluate_regval(value_exprs.get(reg, reg))
    return val

def evaluate_regval(regval):
    """
    Evaluates a value expression into a constant integer value, if possible.
    @returns 'N/A' if not possible to evaluate, otherwise the integer value.
    """
    global initial_env
    if regval == 'top':
        return 'N/A'
    val = 'N/A'
    try:
        #make copy of initial environment
        env = dict(initial_env)
        #TODO - needs to set initial values of registers
        #expr = 'r13 = ' + str(STACK_START) + " ; r13 = " + value_exprs.get('r13', 'r13')
        #expr = 'r13 = ' + str(STACK_START) + " ; " + regname + " = " + value_exprs.get(regname, regname)
        expr = "val = " + regval
        exec expr in env
        val = env['val']
    except Exception, e:
        #print "Couldn't evaluate expression", e
        pass
    return val


def memory_address_from_instruction(f, calling_contexts, weight, ins):
    addrval = "INVALID_ADDRESS"
    arch = f.getArch()
    #helper function
    def get_ins_type(opcode):
        return arch.get_ins_type(opcode)
    def normalize_regname(reg):
        return arch.normalize_regname(reg)
    def regval_from_value_exprs(value_exprs, reg):
        global regval_from_value_exprs
        val = regval_from_value_exprs(value_exprs, reg)
        if val == 'N/A':
            val = 'INVALID_ADDRESS'
        return val

    (regsread, regswrite, values) = arch.parseArguments(ins)
    value_exprs = {}
    for e in map(str.strip, str(weight)[1:-1].split(";")):
        if "=" in e:
            (regname, expr) = map(str.strip, e.split("="))
            value_exprs[regname] = expr
    #print value_exprs
    #import pdb; pdb.set_trace()
    if get_ins_type(ins.getOpcode()) in ['INSTR_PUSH', 'INSTR_POP']:
        addrval = regval_from_value_exprs(value_exprs, "r13")
    elif get_ins_type(ins.getOpcode()) in ['INSTR_STORE', 'INSTR_LOAD', 'INSTR_LOADROTATE']:
        #PC relative load
        if regsread == ['pc'] and len(values) == 1:
            #Calculate address (+8 to account for pipeline)
            addrval = ins.address + 8 + values[0]
        #Load from address contained in single register
        elif (len(regsread) == 1 and len(values) == 0) or \
            (get_ins_type(ins.getOpcode()) == 'INSTR_STORE' and len(regsread) == 2 and len(values) == 0):
            #find value of register
            reg = normalize_regname(regsread[-1])
            addrval = regval_from_value_exprs(value_exprs, reg)
        #Load from address contained in single register, constant offset
        elif (len(regsread) == 1 and len(values) == 1) or \
            (get_ins_type(ins.getOpcode()) == 'INSTR_STORE' and len(regsread) == 2 and len(values) == 1):
            #find value of register
            reg = normalize_regname(regsread[-1])
            #import pdb; pdb.set_trace()
            reg1 = regval_from_value_exprs(value_exprs, reg)
            if not reg1 == 'INVALID_ADDRESS':
                addrval = reg1 + values[0]
        #Load from address contained in two registers (base and offset)
        elif (len(regsread) == 2 and len(values) == 0) or \
            (get_ins_type(ins.getOpcode()) == 'INSTR_STORE' and len(regsread) == 3 and len(values) == 0):
            reg1 = regval_from_value_exprs(value_exprs, regsread[-2])
            reg2 = regval_from_value_exprs(value_exprs, regsread[-1])
            #print "At ", str(ins), "found", reg1, "+", reg2
            if not reg1 == 'INVALID_ADDRESS' and not reg2 == 'INVALID_ADDRESS':
                addrval = reg1 + reg2
        #Load from address contained in two registers (base and offset), left shiftet
        elif (len(regsread) == 2 and len(values) == 1) or \
            (get_ins_type(ins.getOpcode()) == 'INSTR_STORE' and len(regsread) == 3 and len(values) == 1):
            #TODO XXX
            #import pdb; pdb.set_trace()
            reg1 = regval_from_value_exprs(value_exprs, regsread[-2])
            reg2 = regval_from_value_exprs(value_exprs, regsread[-1])
            #print "At ", str(ins), "found", reg1, "+", reg2
            if not reg1 == 'INVALID_ADDRESS' and not reg2 == 'INVALID_ADDRESS':
                addrval = reg1 + reg2
            
    return addrval

def calculate_weight(f, calling_contexts, answer, ins):
    """Calculates the weight associated with this instruction,
    given the calling contexts and the answer.
    """
    #the state of our automaton
    p = wali.getKey("p")

    func = ins.getFunction()
    loop_bounds = find_loopbounds(func)

    if len(loop_bounds.values()) == 0:
        k0 = wali.getKey(hex(ins.address)[:-1] + "_")
        #print hex(ins.address)[:-1] + "_"
        transitions = answer.match(p, k0).asList()
        if len(transitions) == 0:
            return None
        trans = transitions[0]
        #print "extending", calling_contexts[func.getLabel()],
        #print "with", trans.weight(),
        weight = calling_contexts[func.getLabel()].extend(trans.weight())

        #Cast to ConstDom
        weight = dissy.constdom.toConstDom(weight)
        return weight
    else:
        context_dict = {}
        #traverse the different loopbound contexts
        #for lb in all_loopbound_combinations(loop_bounds.values()):
        for lb in loopcontexts_seen[func.getLabel()]:
            print 'lb', lb.values()
            k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                "_".join( map(str, lb.values()) ))

            transitions = answer.match(p, k0).asList()
            assert(len(transitions) in [0, 1])
            if len(transitions) == 1:
                trans = transitions[0]
                #import pdb; pdb.set_trace()
                weight = calling_contexts[func.getLabel()].extend(trans.weight())
                #print "extending", calling_contexts[func.getLabel()], "with", trans.weight(),
                #print "=", weight
                print hex(ins.address), lb, str(ins), weight
                
                #Cast to ConstDom
                weight = dissy.constdom.toConstDom(weight)

                context_dict[tuple(lb.values())] = weight

        return context_dict

def calculate_memaccesses(f, calling_contexts, answer):
    """Calculates the memory address accessed by a memory operation.
    @returns a dict from memory address of instruction -> memory address,
        or -> dict of loop bounds -> memory address, if function uses loop bounds.
    """
    arch = f.getArch()
    #helper function
    def get_ins_type(opcode):
        return arch.get_ins_type(opcode)

    #the state of our automaton
    p = wali.getKey("p")

    toret = {}

    for func in f.getFunctions():
        if func.getLabel()[0:1] == '_':
            continue
        if func.getLabel()[0:2] == '__':
            continue
        if func.getLabel() in ['call_gmon_start', 'frame_dummy']:
            continue
        loop_bounds = find_loopbounds(func)
        for ins in func.getInstructions():
            if get_ins_type(ins.getOpcode()) in \
                ['INSTR_STORE', 'INSTR_LOAD', 'INSTR_PUSH', 'INSTR_POP',
                 'INSTR_LOADROTATE']:
                if len(loop_bounds.values()) == 0:
                    k0 = wali.getKey(hex(ins.address)[:-1] + "_")
                    print hex(ins.address)[:-1] + "_"
                    trans = answer.match(p, k0).asList()[0]
                    #print "extending", calling_contexts[func.getLabel()],
                    #print "with", trans.weight(),
                    weight = calling_contexts[func.getLabel()].extend(trans.weight())
                    #print "=", weight
                    #print hex(ins.address), str(ins), weight
                    #find out address, by evaluating expression, given weight



                    toret[ins.address] = memory_address_from_instruction(f, calling_contexts, weight, ins)
                else:
                    context_dict = {}
                    #traverse the different loopbound contexts
                    for lb in all_loopbound_combinations(loop_bounds.values()):
                        k0 = wali.getKey(hex(ins.address)[:-1] + "_" + \
                            "_".join( map(str, lb) ))
                        transitions = answer.match(p, k0).asList()
                        assert(len(transitions) in [0, 1])
                        if len(transitions) == 1:
                            trans = transitions[0]
                            weight = calling_contexts[func.getLabel()].extend(trans.weight())
                            #print "extending", calling_contexts[func.getLabel()], "with", trans.weight(),
                            #print "=", weight
                            #print hex(ins.address), lb, str(ins), weight
                            addrval = memory_address_from_instruction(f, calling_contexts, weight, ins)
                            if addrval != 'INVALID_ADDRESS':
                                context_dict[lb] = addrval
                    toret[ins.address] = context_dict
    return toret

def do_valueanalysis(fname):
    #construct WPDS
    f = dissy.File.File(fname)
    for func in f.getFunctions():
        func.parse()
        func.link()
    res = construct_wpds(f)

    #Compute the result
    query = wali.WFA()
    p = wali.getKey("p")
    accept = wali.getKey("accept")
    initloc = wali.getKey("f_main")
    query.addTrans( p, initloc  , accept, getNoEffect() );
    query.set_initial_state( p )
    query.add_final_state( accept )
    answer = wali.WFA()
    res.poststar(query, answer)

    #post-process the result
    calling_contexts = calculate_calling_contexts(f, answer)
    mem_accesses = calculate_memaccesses(f, calling_contexts, answer)
    return mem_accesses

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print "Usage: %s objfilename" % (sys.argv[0])
        sys.exit(1)

    fname = sys.argv[1]

    verbose = False
    if len(sys.argv) > 2 and sys.argv[2] == '-v':
        verbose = True
        verbosefile = open('/tmp/value-analysis-out.txt', 'w')

    f = dissy.File.File(fname)
    for func in f.getFunctions():
        func.parse()
        func.link()
    res = construct_wpds(f)

    print "=================== WPDS constructed =============="

    if verbose:
        #Sort output, by address ;-)
        lines = str(res).split("\n")
        lines.sort()
        verbosefile.write("=== WPDS ===\n")
        verbosefile.write('\n'.join(lines))
        verbosefile.write("\n\n\n")

    #TEST
    query = wali.WFA()
    p = wali.getKey("p")
    accept = wali.getKey("accept")
    initloc = wali.getKey("f_main")

    query.addTrans( p, initloc  , accept, getNoEffect() );

    query.set_initial_state( p )
    query.add_final_state( accept )

    if verbose:
        print "============== ANSWER ==============="

    answer = wali.WFA()
    res.poststar(query, answer)
    
    if verbose:
        print "done"
        verbosefile.write("=== Answer ===\n")
        verbosefile.write( str(answer) )
        verbosefile.write("\n\n\n")

    calling_contexts = calculate_calling_contexts(f, answer)
    if verbose:
        verbosefile.write("=== Calling Contexts ===\n")
        for k in calling_contexts:
            verbosefile.write( k + ": " + str(calling_contexts[k]) + "\n")
        verbosefile.write("\n\n\n")

    mem_accesses = calculate_memaccesses(f, calling_contexts, answer)
    if verbose:
        mem_access_addrs = mem_accesses.keys()
        mem_access_addrs.sort()
        verbosefile.write("=== Memory Accesses ===\n")
        for addr in mem_access_addrs:
            #if isinstance(mem_accesses[addr], dict):
            #    print hex(addr)[:-1], ":",
            #    lbcs = mem_accesses[addr].keys()
            #    lbcs.sort()
            #    for lbc in lbcs:
            #        pass
            #        pass
            #        print lbc, ":", mem_accesses[addr][lbc]
            #        #print ""
            #        #a = 42
            #        pass
            #else:
            verbosefile.write(hex(addr)[:-1] + ": " + str(mem_accesses[addr]) + "\n")
        verbosefile.write("\n\n\n")

    #f = open('/tmp/lalala.dot', 'w')
    #f.write(answer.print_dot())
    #f.close()

    sys.exit(0)
