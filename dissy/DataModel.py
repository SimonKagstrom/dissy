######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   Display the functions
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
import gtk, gobject

class InfoModel:
    """ The model class holds the information we want to display """

    def __init__(self, fileContainer):
        """ Sets up and populates our gtk.TreeStore """

        self.tree_store = gtk.TreeStore( gobject.TYPE_STRING,
                                         gobject.TYPE_LONG,
                                         gobject.TYPE_STRING,
                                         gobject.TYPE_PYOBJECT
                                         )
        # Create the TreeStore
        for item in fileContainer.getData():
            # Insert functions
            item.iter = self.tree_store.append(None, ("0x%08x" % item.address,
                                                      item.getSize(),
                                                      item.getLabel(),
                                                      item.getType(),
                                                      item
                                                      ) )

    def getModel(self):
        """ Returns the model """
        if self.tree_store:
            return self.tree_store
        else:
            return None
