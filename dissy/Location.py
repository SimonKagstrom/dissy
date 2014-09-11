######################################################################
##
## Copyright (C) 2009,  Simon Kagstrom
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   A location somewhere
##
## Licensed under the terms of GNU General Public License version 2 or
## later. See COPYING file distributed with Dissy for full text of the
## license.
##
######################################################################
import dissy

class Location:
    def __init__(self, where):
        self.md5 = dissy.File.getMD5()

        fn = dissy.File.lookup(where)
        insn = fn.lookup(where)

        self.insns = []
        try:
            self.insns.append(fn.getPrevInstruction(insn))
        except:
            pass
        self.insns.append(insn)
        try:
            self.insns.append(fn.getNextInstruction(insn))
        except:
            pass
