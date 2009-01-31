######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      InstructionModel.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Instruction models
##
## $Id: InstructionModel.py 12442 2006-11-25 10:14:05Z ska $
##
######################################################################
import gtk, gobject

from Config import *
from Function import Function
from StrEntity import StrEntity

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

def markup(pattern, string, color):
    s = ""
    last = 0
    for i in pattern.finditer(string):
	span = i.span()
	s = s + string[last:span[0]] + '<span foreground="' + color + '">' + string[span[0] : span[1] ] + '</span>'
	last = span[1]
    else:
	s = s + string[last:]
    return s

class InfoModel:
    """ The model class holds the information we want to display """

    def __init__(self, function, markPattern = None):
	""" Sets up and populates our gtk.TreeStore """

	self.markPattern = markPattern
	self.function = function
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
	if function == None:
	    return
	if function.getAll() == []:
	    function.parse()
	    function.link()

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

	    insnStr = insn.getOpcode()
	    argsStr = insn.getArgs()
	    if self.markPattern:
		insnStr = markup(self.markPattern, insnStr, config.markupFgColor)
		argsStr = markup(self.markPattern, argsStr, config.markupFgColor)
	    strRepresentation = '<span foreground="%s">%s</span>\t%s' % (config.insnFgColor, insnStr, argsStr)
	    insn.iter = self.tree_store.append( None, ("0x%08x" % insn.getAddress(),
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

    def getModel(self):
	""" Returns the model """
	if self.tree_store:
	    return self.tree_store
	else:
	    return None
