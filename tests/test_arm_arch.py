#!/usr/bin/python
import sys
import os.path
import unittest
projdir = os.path.normpath(os.path.join(os.path.dirname(sys.argv[0]), '..'))
sys.path = [projdir] + sys.path
import dissy.architecture
from dissy.arm import ArmArchitecture
from dissy.Instruction import Instruction


def instr(opcode, args):
    #mock of function + file object
    class MockFunction():
        def __init__(self):
            self.baseAddress = 0
            self.arch = ArmArchitecture()
        def getFile(self):
            return self
        def getArch(self):
            return self.arch
    return Instruction(MockFunction(), 0, None, opcode, args)

class TestArmArch(unittest.TestCase):
    def setUp(self):
        self.arch = ArmArchitecture()
        self.assertNotEqual(self.arch, None)

    def test_arg_parsing(self):
        self.assertEqual(self.arch.parseArguments(instr('mov', 'r8, #6')),
            ([], ['r8'], [6]))
        self.assertEqual(self.arch.parseArguments(instr('mov', 'ip, #0')),
            ([], ['ip'], [0]))
        self.assertEqual(self.arch.parseArguments(instr('movle', 'r0, #1')),
            ([], ['r0'], [1]))
        self.assertEqual(self.arch.parseArguments(instr('cmp', 'r0, #1')),
            (['r0'], [], [1]))

        #Add og sub
        self.assertEqual(self.arch.parseArguments(instr('sub', 'sp, sp, #4')),
            (['sp'], ['sp'], [4]))
        self.assertEqual(self.arch.parseArguments(instr('add', 'sp, sp, #4')),
            (['sp'], ['sp'], [4]))
        self.assertEqual(self.arch.parseArguments(instr('add', 'r2, r2, #1')),
            (['r2'], ['r2'], [1]))
        self.assertEqual(self.arch.parseArguments(instr('addlt', 'r5, r5, r3')),
            (['r5', 'r3'], ['r5'], []))
        self.assertEqual(self.arch.parseArguments(instr('sub', 'r3, r3, r0, lsl #2')),
            (['r3', 'r0'], ['r3'], []))

        #shifts
        self.assertEqual(self.arch.parseArguments(instr('lsl', 'r1, r3, #7')),
            (['r3'], ['r1'], [7]))
        self.assertEqual(self.arch.parseArguments(instr('asr', 'r1, r2, #31')),
            (['r2'], ['r1'], [31]))
        self.assertEqual(self.arch.parseArguments(instr('rsb', 'r0, r1, r0, asr #9')),
            (['r1', 'r0'], ['r0'], []))
        self.assertEqual(self.arch.parseArguments(instr('lsl', 'r1, r3, #7')),
            (['r3'], ['r1'], [7]))

        #branches
        self.assertEqual(self.arch.parseArguments(instr('bl', '0')),
            ([], ['pc', 'lr'], []))
        self.assertEqual(self.arch.parseArguments(instr('bx', 'lr')),
            (['lr'], ['pc'], []))
        self.assertEqual(self.arch.parseArguments(instr('ble', '4c')),
            ([], ['pc'], []))

        #Dynamisk load
        self.assertEqual(self.arch.parseArguments(instr('ldr', 'r3, [ip]')),
            (['ip'], ['r3'], []))
        self.assertEqual(self.arch.parseArguments(instr('ldr', 'r3, [pc, #8]')),
            (['pc'], ['r3'], []))
        self.assertEqual(self.arch.parseArguments(instr('ldr', 'r3, [r2, r0]')),
            (['r2', 'r0'], ['r3'], []))
        self.assertEqual(self.arch.parseArguments(instr('ldm', 'r0, {r0, r1}')),
            (['r0'], ['r0', 'r1'], []))
        #Dynamisk store
        self.assertEqual(self.arch.parseArguments(instr('str', 'r0, [r3]')),
            (['r0', 'r3'], [], []))
        self.assertEqual(self.arch.parseArguments(instr('str', 'r0, [r4, r5]')),
            (['r0', 'r4', 'r5'], [], []))
        self.assertEqual(self.arch.parseArguments(instr('stm', 'sp, {r2, r3}')),
            (['sp', 'r2', 'r3'], [], []))

        #unimplemented instruction type
        self.assertRaises(ValueError, self.arch.parseArguments, instr('abemad', 'r1, r0'))

        #multiplication
        self.assertEqual(self.arch.parseArguments(instr('smull', 'r1, r0, r3, r2')),
            (['r3', 'r2'], ['r1', 'r0'], []))

        #multiplication
        self.assertEqual(self.arch.parseArguments(instr('mul', 'r0, r3, r2')),
            (['r3', 'r2'], ['r0'], []))
        self.assertEqual(self.arch.parseArguments(instr('mla', 'r1, r2, r3, r1')),
            (['r2', 'r3', 'r1'], ['r1'], []))

        #Push, pop
        self.assertEqual(self.arch.parseArguments(instr('push', '{lr}')),
            (['sp', 'lr'], ['sp'], []))
        self.assertEqual(self.arch.parseArguments(instr('push', '{r4, r5, lr}')),
            (['sp', 'r4', 'r5', 'lr'], ['sp'], []))
        self.assertEqual(self.arch.parseArguments(instr('pop', '{r4, r5, lr}')),
            (['sp'], ['sp', 'r4', 'r5', 'lr'], []))
        self.assertEqual(self.arch.parseArguments(instr('pop', '{lr}')),
            (['sp'], ['sp', 'lr'], []))

        #Assorted
        self.assertEqual(self.arch.parseArguments(instr('and', 'r3, r3, #31')),
            (['r3'], ['r3'], [31]))
        self.assertEqual(self.arch.parseArguments(instr('muls', 'r3, r4, r3')),
            (['r4', 'r3'], ['r3'], []))

if __name__ == '__main__':
    unittest.main()
