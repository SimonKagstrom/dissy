######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Base-class for architecture handling
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
class Architecture:
    """
    Architecture base class. Inherit this to implement
    architecture-specific handling (see intel.py and mips.py)
    """
    def __init__(self, arch_jumps = [], arch_calls = []):
        self.jumps = {}
        self.calls = {} # To handle reverse-engineering
        for s in arch_jumps:
            self.jumps[s.strip()] = True
        for s in arch_calls:
            self.calls[s.strip()] = True

    def isJump(self, insn):
        "Returns true if this instruction is a jump"
        return insn in self.jumps

    def isCall(self, insn):
        "Returns true if this instruction is a call"
        return insn in self.calls

    def getJumpDestination(self, insn, args):
        """Parse the instruction to return the jump destination. The
        base class only tries to convert the argument to a number. See
        mips.py for a more advanced translation.
        """
        try:
            return long(args, 16)
        except ValueError:
            pass
        return None

from dissy import mips, intel, ppc, arm

def getArchitecture(archStr):
    if archStr == "intel":
        return intel.IntelArchitecture()
    elif archStr == "x86-64":
        return intel.IntelArchitecture()
    elif archStr == "i8086":
        return intel.IntelArchitecture()
    if archStr == "mips":
        return mips.MipsArchitecture()
    if archStr == "ppc":
        return ppc.PpcArchitecture()
    if archStr == "powerpc":
        return ppc.PpcArchitecture()
    if archStr == "arm":
        return arm.ArmArchitecture()
    if archStr == "arm26":
        return arm.ArmArchitecture()
    return Architecture([])
