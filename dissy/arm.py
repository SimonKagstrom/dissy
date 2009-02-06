######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      arm.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Arm arch specific stuff
##
## $Id: arm.py 14169 2007-03-11 14:43:02Z ska $
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

class ArmArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, arm_jumps, arm_calls)
