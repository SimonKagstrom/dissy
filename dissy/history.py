######################################################################
##
## Copyright (C) 2007,  Simon Kagstrom
##
## Filename:      history.py
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   History implementation
##
## $Id:$
##
######################################################################
class History:
    def __init__(self):
        self.history = []
        self.index = 0
        self.enabled = True

    def add(self, entry):
        "Add an entry to the history"
        # Don't add twice
        if not self.enabled or self.history != [] and self.history[self.index-1] == entry:
            return None
	if self.index == 1 and len(self.history) > 1:
	    self.history = []
	    self.index = 0

	self.history = self.history[ : self.index] + [entry]
	self.index = self.index + 1
        return entry

    def enable(self):
        self.enabled = True

    def disable(self):
        self.enabled = False

    def back(self):
        "Go back one step"
	if self.index-1 <= 0:
            raise Exception("End of history")
        self.index = self.index - 1
        return self.history[self.index-1]

    def forward(self):
        "Go forward one step"
        if self.index >= len(self.history):
            raise Exception("End of history")
        self.index = self.index + 1
        return self.history[self.index-1]

    def current(self):
        "Get the current entry"
        return self.history[self.index]

    def isFirst(self):
        "Is this the first entry?"
        return self.index <= 0

    def isLast(self):
        "Is this the last entry?"
        return self.index >= len(self.history)

    def getAllEntries(self):
        "Return everything in the current history"
        return self.history

if __name__ == "__main__":
    h = History()
    print "Adding some entries"
    h.add(1)
    h.add(2)
    h.add(3)
    print h.getAllEntries()
    print "Back one step:", h.back()
    h.add(4)
    print "Add, all entries:", h.getAllEntries()
    print "Back two, forward"
    print h.back()
    print h.back()
    try:
        # Should raise
        print h.back()
    except:
        print "Got expected exception (back)"
    print h.forward()
    print h.forward()
    try:
        print h.forward()
    except:
        print "Got expected exception (fwd)"
    print "All entries", h.getAllEntries()
    h.back()
    h.back()
    h.add(5)
    print h.getAllEntries()
    h.add(6)
    print h.getAllEntries()
