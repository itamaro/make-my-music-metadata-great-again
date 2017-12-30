#!/usr/bin/env python3
# Copyright 2017 Itamar Ostricher

"""Make My Music Metadata Great Again.

Usage:
  mmmmga.py [--dir <dir>] [--no-delete] [--force]
  mmmmga.py (-h | --help)
  mmmmga.py --version

Options:
  -h --help     Show this screen.
  --version     Show version.
  --dir <dir>   Start scanning from this directory [default: .].
  --no-delete   If specified, will avoid deletions.
  --force       If specified, will also process already finished albums.
"""

from docopt import docopt

import colorama
import requests

from .mmmmga import run


if '__main__' == __name__:
  colorama.init(autoreset=True)
  arguments = docopt(__doc__, version='Make My Music Metadata Great Again 0.1')
  run(arguments['--dir'], arguments['--no-delete'], arguments['--force'])
