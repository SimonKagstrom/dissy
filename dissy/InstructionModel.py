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

from Config import *
from Function import Function
from StrEntity import StrEntity
from Instruction import Instruction

def loadFile(fileName):
    pathsToSearch = ['.', '/usr/local/share/%s' % (PROGRAM_NAME).lower(),
                     '/usr/share/%s' % (PROGRAM_NAME).lower()]
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

(
COLUMN_ADDR,
COLUMN_LEFT_STATE2,
COLUMN_LEFT_STATE1,
COLUMN_LEFT_STATE0,
COLUMN_STR_REPRESENTATION,
COLUMN_RIGHT_STATE0,
COLUMN_RIGHT_STATE1,
COLUMN_RIGHT_STATE2,
COLUMN_TARGET,
COLUMN_INSTRUCTION,
) = range(10)

class InfoModel:
    """ The model class holds the information we want to display """

    def __init__(self, function, curInstruction = None, highlighters=[]):
        """ Sets up and populates our gtk.TreeStore """

        self.function = function
        self.curInstruction = curInstruction
        self.highlighters = highlighters
        self.tree_store = gtk.TreeStore( gobject.TYPE_STRING,
                                         gtk.gdk.Pixbuf,
                                         gtk.gdk.Pixbuf,
                                         gtk.gdk.Pixbuf,
                                         gobject.TYPE_STRING,
                                         gtk.gdk.Pixbuf,
                                         gtk.gdk.Pixbuf,
                                         gtk.gdk.Pixbuf,
                                         gobject.TYPE_STRING,
                                         gobject.TYPE_PYOBJECT
                                         )
        # Create the TreeStore
        if self.function == None:
            return
        self.lazyinitFunction()

        for insn in self.function.getAll():
            if isinstance(insn, StrEntity):
                if config.showHighLevelCode:
                    insn.iter = self.tree_store.append( None, ("",
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

            insnAddr = "0x%08x" % (insn.getAddress())
            insnStr = insn.getOpcode()
            argsStr = insn.getArgs()

            strRepresentation = '<span foreground="%s">%s</span>\t%s' % (config.insnFgColor, insnStr, argsStr)
            insn.iter = self.tree_store.append( None, (insnAddr,
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
        self.refreshModel()

    def refreshModel(self):
        for iter in self.tree_store:
            insn = iter[COLUMN_INSTRUCTION]
            if isinstance(insn, Instruction):
                insnAddr = "0x%08x" % (insn.getAddress())
                insnStr = insn.getOpcode()
                argsStr = insn.getArgs()
                strRepresentation = '<span foreground="%s">%s</span>\t%s' % (config.insnFgColor, insnStr, argsStr)
                if insn.comment:
                    strRepresentation += ' <span foreground="%s">;%s</span>' % (config.highLevelCodeFgColor, insn.comment)
                iter[COLUMN_STR_REPRESENTATION] = strRepresentation
                iter[COLUMN_ADDR] = insnAddr
                for highlighter in self.highlighters:
                    highlighter.highlight(iter, self.curInstruction)

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
