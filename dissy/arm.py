######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <ska@bth.se>
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

class ArmArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, arm_jumps, arm_calls)
