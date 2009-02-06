######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <simon.kagstrom@gmail.com>
## Description:   String entity
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
from dissy.Entity import Entity

class StrEntity(Entity):
    def __init__(self, fn, string):
        self.string = string
        self.function = fn

    def getFunction(self):
        return self.function

    def __str__(self):
        return self.string
