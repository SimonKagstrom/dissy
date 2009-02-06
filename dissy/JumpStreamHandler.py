######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Jump streams
##
## Licensed under the terms of GNU General Public License version 2
## (or later, at your option). See COPYING file distributed with Dissy
## for full text of the license.
##
######################################################################
INVALID=0
START=1
RUNNING=2
END=3
EXTRA=4
EXTRA2=5

class JumpStream:
    def __init__(self):
        self.state = INVALID
        self.insnTuple = (None,None)
    def start(self, insnTuple):
        self.state = START
        self.insnTuple = insnTuple
    def running(self):
        self.state = RUNNING
    def end(self):
        self.state = END
    def invalid(self):
        self.state = INVALID
    def extra(self):
        self.state = EXTRA
    def extra2(self):
        self.state = EXTRA2

class JumpStreamHandler:
    def __init__(self):
        self.streams = []
        for i in range(0,3):
            self.streams.append(JumpStream())
    def alloc(self):
        for stream in self.streams:
            if stream.state == INVALID or stream.state == END:
                return stream
        for stream in self.streams:
            stream.extra()
        return None
    def update(self, insn):
        for stream in self.streams:
            if stream.state == START and insn != stream.insnTuple[0]:
                stream.running()
            elif stream.state == END:
                stream.invalid()
            elif stream.state == EXTRA:
                stream.extra2()
            elif stream.state == EXTRA2:
                stream.running()
            # If this is the destination, switch to the end state
            if insn == stream.insnTuple[1]:
                stream.end()
    def getStateTuple(self):
        return (self.streams[0].state, self.streams[1].state, self.streams[2].state)
