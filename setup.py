######################################################################
##
## Copyright (C) 2006,  Blekinge Institute of Technology
##
## Filename:      setup.py
## Author:        Simon Kagstrom <ska@bth.se>
## Description:   Installation script
##
## $Id: setup.py 14502 2007-03-28 04:21:14Z ska $
##
######################################################################
import sys

sys.path.append(".")
from dissy import Config

from distutils.core import setup

setup(name='%s' % (Config.PROGRAM_NAME).lower(),
      version='%s' % (Config.PROGRAM_VERSION),
      description="A graphical frontend to objdump with navigation possibilities",
      author="Simon Kagstrom",
      url="%s" % (Config.PROGRAM_URL),
      author_email="simon.kagstrom@bth.se",

      packages = ['dissy'],
      scripts = ['scripts/dissy'],

      data_files = [('share/%s/gfx' % (Config.PROGRAM_NAME.lower()),
		     ['gfx/red_arrow_left.png', 'gfx/red_line.png', 'gfx/red_start_down.png',
		      'gfx/red_arrow_right.png', 'gfx/red_plus.png', 'gfx/red_start_up.png']),
		    ('share/%s/' % (Config.PROGRAM_NAME.lower()), ['menubar.xml']),
		    ('share/doc/%s/' % (Config.PROGRAM_NAME.lower()), ['README']),
		    ('share/doc/%s/' % (Config.PROGRAM_NAME.lower()), ['COPYING']),
		    ('share/man/man1/', ['dissy.1']),
		    ],
      )

