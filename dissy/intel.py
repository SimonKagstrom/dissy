######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      intel.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Intel arch specific stuff
##
## $Id: intel.py 14169 2007-03-11 14:43:02Z ska $
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
