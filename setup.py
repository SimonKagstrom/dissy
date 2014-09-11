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
import os.path

sys.path.append(".")
from dissy import Config

from distutils.core import setup, Extension

extensions = []
WALI_INCLUDE_DIR = ""
WALI_LIB_DIR = ""
for arg in sys.argv:
    if arg.startswith('--with-uninstalled-wali='):
        WALI_INCLUDE_DIR = os.path.join(
            arg[len('--with-uninstalled-wali='):], 'Source')
        WALI_LIB_DIR = os.path.join(
            arg[len('--with-uninstalled-wali='):], 'lib')

        print 'Building with value analysis support'
        extensions += [Extension('_constdom', ['dissy/constdom.i'],
            libraries=['wali'], 
            include_dirs=[ WALI_INCLUDE_DIR ],
            extra_link_args=['-L' + WALI_LIB_DIR],
            #define_macros=macros,
            #extra_compile_args=compilerArgs, 
            #language=lang, 
            swig_opts=['-c++', '-I' + WALI_INCLUDE_DIR])]
        sys.argv.remove(arg)

setup(name='%s' % (Config.PROGRAM_NAME).lower(),
      version='%s' % (Config.PROGRAM_VERSION),
      description="A graphical frontend to objdump with navigation possibilities",
      author="Simon Kagstrom",
      url="%s" % (Config.PROGRAM_URL),
      author_email="simon.kagstrom@gmail.com",

      packages = ['dissy'],
      scripts = ['scripts/dissy'],

      data_files = [('share/%s/gfx' % (Config.PROGRAM_NAME.lower()),
             ['gfx/red_arrow_left.png', 'gfx/red_line.png', 'gfx/red_start_down.png',
              'gfx/red_arrow_right.png', 'gfx/red_plus.png', 'gfx/red_start_up.png',
                      'gfx/icon.svg']),
		    ('share/%s/' % (Config.PROGRAM_NAME.lower()), ['dissy.ui']),
		    ('share/doc/%s/' % (Config.PROGRAM_NAME.lower()), ['README']),
		    ('share/doc/%s/' % (Config.PROGRAM_NAME.lower()), ['COPYING']),
		    ('share/man/man1/', ['dissy.1']),
		    ],
      )

