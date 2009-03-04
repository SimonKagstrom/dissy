######################################################################
##
## Copyright (C) 2009, Mads Chr. Olesen
##
## Author:        Mads Chr. Olesen <mads@mchro.dk>
## Description:   Filter-decorator for InstructionModel
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################

from Config import *
from dissy import InstructionModel
from Instruction import Instruction
import re

class InstructionModelHighlighter:
    def __init__(self):
        pass

    def highlight(self, row, curInstruction):
        """Possibly modify the columns of row"""
        pass

class SearchwordHighlighter(InstructionModelHighlighter):
    """Highlights anything that matches the regular expression given"""
    def __init__(self, searchPattern=None):
        InstructionModelHighlighter.__init__(self)
        self.setSearchPattern(searchPattern)

    def setSearchPattern(self, searchPattern):
        if searchPattern:
            #Match anything not in a tag (> occurs after match, but before a <)
            self.searchPattern = re.compile(searchPattern + "(?![^<]*>)")
        else:
            self.searchPattern = None

    def markup(self, pattern, string, color):
        s = ""
        last = 0
        for i in pattern.finditer(string):
            span = i.span()
            s = s + string[last:span[0]] + '<span foreground="' + color + '">' + string[span[0] : span[1] ] + '</span>'
            last = span[1]
        else:
            s = s + string[last:]
        return s

    def highlight(self, row, curInstruction):
        insn = row[InstructionModel.COLUMN_INSTRUCTION]
        strRep = row[InstructionModel.COLUMN_STR_REPRESENTATION]
        if self.searchPattern:
            strRep = self.markup(self.searchPattern, strRep, config.markupFgColor)
        row[InstructionModel.COLUMN_STR_REPRESENTATION] = strRep

class ConditionFlagHighlighter(InstructionModelHighlighter):
    """Highlights the instruction that may have set the processor condition
    flags."""

    def __init__(self):
        InstructionModelHighlighter.__init__(self)
        
    def highlight(self, row, curInstruction):
        if not curInstruction:
            return
        insn = row[InstructionModel.COLUMN_INSTRUCTION]
        arch = curInstruction.getFunction().getFile().getArch()
        #import pdb; pdb.set_trace()

        if not arch.isConditionFlagSetter(insn.getOpcode()) or \
            not arch.isConditionFlagUser(curInstruction.getOpcode()):
            return
        if curInstruction == insn:
            return
        inthezone = False
        for i in curInstruction.getFunction().getAll():
            if not isinstance(i, Instruction):
                continue
            if inthezone and arch.isConditionFlagSetter(i.getOpcode()):
                return
            if i == insn:
                inthezone = True
            if inthezone and i == curInstruction:
                row[InstructionModel.COLUMN_ADDR] = '<span foreground="green">' + \
                    row[InstructionModel.COLUMN_ADDR] + \
                    '</span>'
