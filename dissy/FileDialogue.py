######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      FileDialogue.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   File dialogue
##
## $Id: FileDialogue.py 8375 2006-05-30 08:59:01Z ska $
##
######################################################################
import pygtk, dissy

pygtk.require('2.0')
import gtk, gobject

from dissy.Config import *
from dissy.File import File
import dissy.FunctionModel

class FileDialogue:
    def __init__(self, controller):
	filesel = gtk.FileSelection(title=None)
	# Connect the ok_button to file_ok_sel method
	filesel.ok_button.connect("clicked", self.okSelected, filesel, controller)

	# Connect the cancel_button to destroy the file selector widget
	filesel.cancel_button.connect("clicked",
				      lambda w: filesel.destroy())
	filesel.show()

    def okSelected(self, widget, filesel, controller):
	name = filesel.get_filename()

	filesel.destroy()

	controller.loadFile(name)
