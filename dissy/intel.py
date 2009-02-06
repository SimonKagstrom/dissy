######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Intel arch specific stuff
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import sys, architecture
from dissy.architecture import Architecture

intel_jumps = ['jbe',
               'jle',
               'jge',
               'jg',
               'je',
               'jb',
               'jz',
               'jne',
               'jnz',
               'jns',
               'js',
               'jmp',
               'ja',
               'jl',
               'call'
               ]
intel_calls = ['call']

class IntelArchitecture(architecture.Architecture):
    def __init__(self):
        architecture.Architecture.__init__(self, intel_jumps, intel_calls)
