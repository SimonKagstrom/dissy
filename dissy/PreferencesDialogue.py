######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Preferences dialog
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import pygtk

# General warning: The code in this file is pure horror! Go somewhere else
# if you suffer from heart problems.

pygtk.require('2.0')
import gtk, gobject

from Config import *

def colorToString(color):
    return "#%04x%04x%04x" % (color.red, color.green, color.blue)

class PreferencesDialogue:
    def __init__(self, main_program):
        self.main_program = main_program

        dialog = gtk.Dialog("%s - Preferences" % (PROGRAM_NAME))
        defaults = gtk.Button("Defaults")
        cancel = gtk.Button("Cancel", gtk.STOCK_CANCEL)
        ok = gtk.Button("OK", gtk.STOCK_OK)

        table = gtk.Table(3, 3, False)
        objdump = gtk.Entry()
        readelf = gtk.Entry()
        nm = gtk.Entry()
        insnColor = gtk.ColorButton(gtk.gdk.color_parse(config.insnFgColor))
        markupColor = gtk.ColorButton(gtk.gdk.color_parse(config.markupFgColor))
        highLevelColor = gtk.ColorButton(gtk.gdk.color_parse(config.highLevelCodeFgColor))

        showHighLevel = gtk.CheckButton("Show high level code")
        showInstructionInfo = gtk.CheckButton("Show instruction information")

        cancel.connect("clicked", lambda w: dialog.destroy())
        ok.connect("clicked", self.okSelected,
                   dialog, objdump, readelf, nm, showHighLevel,
                   showInstructionInfo, insnColor, markupColor, highLevelColor)
        defaults.connect("clicked", self.defaultsSelected,
                         objdump, readelf, nm, showHighLevel, showInstructionInfo,
                         insnColor, markupColor, highLevelColor)

        objdump.set_text(config.objdump)
        readelf.set_text(config.readelf)
        nm.set_text(config.nm)

        showHighLevel.set_active(config.showHighLevelCode)
        showInstructionInfo.set_active(config.showInstructionInformationBox)

        table.attach(gtk.Label("Objdump:"), 0, 1, 0, 1,  ypadding=2)
        table.attach(gtk.Label("Readelf:"), 0, 1, 1, 2,  ypadding=2)
        table.attach(gtk.Label("nm:"), 0, 1, 2, 3,  ypadding=2)

        table.attach(gtk.Label("Instruction color:"), 0, 1, 3, 4,  ypadding=2)
        table.attach(gtk.Label("Highlight color:"), 0, 1, 4, 5,  ypadding=2)
        table.attach(gtk.Label("High-level code color:"), 0, 1, 5, 6,  ypadding=2)

        table.attach(objdump, 1, 2, 0, 1,  ypadding=2)
        table.attach(readelf, 1, 2, 1, 2,  ypadding=2)
        table.attach(nm, 1, 2, 2, 3,  ypadding=2)

        table.attach(insnColor, 1, 2, 3, 4,  ypadding=2)
        table.attach(markupColor, 1, 2, 4, 5,  ypadding=2)
        table.attach(highLevelColor, 1, 2, 5, 6,  ypadding=2)

        table.attach(showHighLevel, 0, 2, 6, 7,  ypadding=6)
        table.attach(showInstructionInfo, 0, 2, 7, 8,  ypadding=6)

        dialog.vbox.pack_start(table, True, True, 0)
        dialog.action_area.pack_start(defaults, True, True, 0)
        dialog.action_area.pack_start(cancel, True, True, 0)
        dialog.action_area.pack_start(ok, True, True, 0)
        dialog.show_all()

    def defaultsSelected(self, widget, objdump, readelf, nm, showHighLevel, showInstructionInfo, insnColor, markupColor, highLevelColor):
        config.restoreAllDefaults()
        objdump.set_text(config.objdump)
        readelf.set_text(config.readelf)
        nm.set_text(config.nm)

        insnColor.set_color( gtk.gdk.color_parse(config.getDefault("insnFgColor")) )
        markupColor.set_color( gtk.gdk.color_parse(config.getDefault("markupFgColor")) )
        highLevelColor.set_color( gtk.gdk.color_parse(config.getDefault("highLevelCodeFgColor")) )

        showHighLevel.set_active(config.showHighLevelCode)
        showInstructionInfo.set_active(config.showInstructionInfo)

    def okSelected(self, widget, dialog, objdump, readelf, nm,
                   showHighLevelCode, showInstructionInfo, insnColor, markupColor, highLevelColor):
        if objdump.get_text() == "":
            config.objdump = config.getDefault("objdump")
        else:
            config.objdump = objdump.get_text()

        if readelf.get_text() == "":
            config.readelf = config.getDefault("readelf")
        else:
            config.readelf = readelf.get_text()

        if nm.get_text() == "":
            config.nm = config.getDefault("nm")
        else:
            config.nm = nm.get_text()

        config.insnFgColor = colorToString(insnColor.get_color())
        config.markupFgColor = colorToString(markupColor.get_color())
        config.highLevelCodeFgColor = colorToString(highLevelColor.get_color())

        config.showHighLevelCode = showHighLevelCode.get_active()
        config.showInstructionInformationBox = showInstructionInfo.get_active()
        config.save()

        dialog.destroy()
        self.main_program.setInformationBox()

