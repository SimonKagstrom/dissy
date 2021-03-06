######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Instruction models
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import gtk, gobject
import cgi

from Config import *
from Function import Function
from StrEntity import StrEntity
from Instruction import Instruction

def loadFile(fileName):
    for path in pathsToSearch:
        fullPath = "%s/%s" % (path, fileName)
        try:
            return gtk.gdk.pixbuf_new_from_file(fullPath)
        except:
            pass
    return None


red_start_down = loadFile("gfx/red_start_down.png")
red_line = loadFile("gfx/red_line.png")
red_plus = loadFile("gfx/red_plus.png")
red_arrow_left = loadFile("gfx/red_arrow_left.png")
red_start_up = loadFile("gfx/red_start_up.png")
red_arrow_right = loadFile("gfx/red_arrow_right.png")

jump_pixmaps_right=[None, red_start_down, red_line, red_arrow_left, red_plus, red_plus]
jump_pixmaps_left=[None, red_start_up, red_line, red_arrow_right, red_plus, red_plus]

class InfoModel:
    """ The model class holds the information we want to display """

    def __init__(self, function, curInstruction = None, highlighters=[], numJumpCols=3):
        """ Sets up and populates our gtk.TreeStore """

        self.function = function
        self.curInstruction = curInstruction
        self.highlighters = highlighters
        cols = [ gobject.TYPE_STRING, ] + \
            [gtk.gdk.Pixbuf]*numJumpCols + \
            [ gobject.TYPE_STRING, ] + \
            [gtk.gdk.Pixbuf]*numJumpCols + \
            [ gobject.TYPE_STRING, gobject.TYPE_PYOBJECT ]

        self.COLUMN_ADDR = 0
        self.COLUMN_STR_REPRESENTATION = 1 + numJumpCols
        self.COLUMN_TARGET = 1 + numJumpCols + 1 + numJumpCols
        self.COLUMN_INSTRUCTION = 1 + numJumpCols + 1 + numJumpCols + 1
        self.tree_store = gtk.ListStore(*cols)
        # Create the TreeStore
        if self.function == None:
            return
        self.lazyinitFunction()

        for insn in self.function.getAll():
            if isinstance(insn, StrEntity):
                if config.showHighLevelCode:
                    insn.iter = self.tree_store.append( ("",
                                                               jump_pixmaps_left[insn.left_state[2]],
                                                               jump_pixmaps_left[insn.left_state[1]],
                                                               jump_pixmaps_left[insn.left_state[0]],
                                                               '<small><span foreground="%s">%s</span></small>\t' % (config.highLevelCodeFgColor, str(insn)),
                                                               jump_pixmaps_right[insn.right_state[0]],
                                                               jump_pixmaps_right[insn.right_state[1]],
                                                               jump_pixmaps_right[insn.right_state[2]],
                                                               "",
                                                               insn
                                                               ))
                continue

            target = ""
            if isinstance(insn.getOutLink(), Function):
                target = insn.getOutLink().getLabel()

            insnAddr = "0x%08x" % (insn.address)
            insnStr = insn.getOpcode()
            argsStr = insn.getArgs()

            strRepresentation = '<span foreground="%s">%s</span>\t%s' % (config.insnFgColor, insnStr, argsStr)
            if insn.comment:
                strRepresentation += ' <span foreground="%s">;%s</span>' % (config.highLevelCodeFgColor, cgi.escape(insn.comment))
            insn.iter = self.tree_store.append( (insnAddr,
                                                       jump_pixmaps_left[insn.left_state[2]],
                                                       jump_pixmaps_left[insn.left_state[1]],
                                                       jump_pixmaps_left[insn.left_state[0]],
                                                       strRepresentation,
                                                       jump_pixmaps_right[insn.right_state[0]],
                                                       jump_pixmaps_right[insn.right_state[1]],
                                                       jump_pixmaps_right[insn.right_state[2]],
                                                       target,
                                                       insn
                                                       ))

    def refreshModel(self):
        for iter in self.tree_store:
            insn = iter[self.COLUMN_INSTRUCTION]
            if isinstance(insn, Instruction):
                insnAddr = "0x%08x" % (insn.address)
                insnStr = insn.getOpcode()
                argsStr = insn.getArgs()
                strRepresentation = '<span foreground="%s">%s</span>\t%s' % (config.insnFgColor, insnStr, argsStr)
                if insn.comment:
                    strRepresentation += ' <span foreground="%s">;%s</span>' % (config.highLevelCodeFgColor, cgi.escape(insn.comment))
                iter[self.COLUMN_STR_REPRESENTATION] = strRepresentation
                iter[self.COLUMN_ADDR] = insnAddr
                for highlighter in self.highlighters:
                    highlighter.highlight(iter, self.curInstruction, self)

    def lazyinitFunction(self):
        if self.function == None:
            return
        if self.function.getAll() == []:
            self.function.parse()
            self.function.link()

    def setCurInstruction(self, curInstruction):
        self.curInstruction = curInstruction
        if self.function == None:
            return

    def getModel(self):
        """ Returns the model """
        if self.tree_store:
            return self.tree_store
        else:
            return None
