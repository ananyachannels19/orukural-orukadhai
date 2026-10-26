import sys

from orukural import brewlibs

brewlibs.ensure(["-m", "pytest"] + sys.argv[1:])
