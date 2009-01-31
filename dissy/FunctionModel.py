######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      FunctionModel.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Display the functions
##
## $Id: FunctionModel.py 8500 2006-06-12 14:03:16Z ska $
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
	for item in fileContainer.getFunctions():
	    # Insert functions
	    item.iter = self.tree_store.append(None, ("0x%08x" % item.getAddress(),
						      item.getSize(),
						      item.getLabel(),
						      item
						      ) )

    def getModel(self):
        """ Returns the model """
        if self.tree_store:
            return self.tree_store
        else:
            return None
