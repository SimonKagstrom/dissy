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
        file_open_dialog = gtk.FileChooserDialog(title="Open object file",
            action=gtk.FILE_CHOOSER_ACTION_OPEN,
                buttons=(gtk.STOCK_CANCEL,
                        gtk.RESPONSE_CANCEL,
                        gtk.STOCK_OPEN,
                        gtk.RESPONSE_OK))
        filter = gtk.FileFilter()
        filter.set_name("Object files")
        filter.add_pattern("*.o")
        filter.add_mime_type("application/x-object")
        filter.add_mime_type("application/x-executable")
        file_open_dialog.add_filter(filter)
        filter = gtk.FileFilter()
        filter.set_name("All files")
        filter.add_pattern("*")
        file_open_dialog.add_filter(filter)

        if file_open_dialog.run() == gtk.RESPONSE_OK:
            filename = file_open_dialog.get_filename()
            controller.loadFile(filename)
            file_open_dialog.destroy()
        else:
            file_open_dialog.destroy()
            return
