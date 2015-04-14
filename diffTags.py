#!/bin/env python

import commands
import os, sys


cmssw = os.environ.get("CMSSW_BASE")
if cmssw == None:
    print "\nError: CMSSW must be properly setup. Quitting.\n"
    sys.exit(1)

cwd = os.environ.get("PWD")
outputFile = ('%s/%s') % (cwd,'diff.log')
w = open(outputFile,'w')
exec_command = "showtags -r | grep ^V | gawk '%s'" % ('{system("cvs diff -r"$2 " -r"$1 " " $3 )}')
out = commands.getoutput(exec_command)
for line in out:
    w.write(line)
w.close()
