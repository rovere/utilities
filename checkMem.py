#!/usr/bin/env python

import os
import re
import time
import sys
import commands
import subprocess
from threading import Thread
from optparse import OptionParser

class memit(Thread):
    def __init__(self,command, options):
        Thread.__init__(self)
        self.command = command
        self.status = -1
        self.report = ''
        self.pid = -1
        self.subproc = None
        self.f = None
        self.exitcode = 0
        self.options = options
    def run(self):
        logfile='checkMem.log'
        if self.options.verbose:
            print 'Opening logfile %s' % logfile
        f=open(logfile,'w')

        if self.options.verbose:
            print "Starting subprocess"
        p3 = subprocess.Popen(self.command, shell=True, stderr=subprocess.STDOUT, stdout=f)
        self.pid = p3.pid
        if self.options.verbose:
            print "Subprocess started with pid %s" % self.pid
        self.subproc = p3
        self.f = f
        exitcode = os.waitpid(p3.pid,0)
        self.exitcode = exitcode[1]
        if self.options.verbose:
            print "Exit code is ", self.exitcode

def main(options, args) :

    if options.verbose:
        print "Opening memory.out file"
    fout=open('memory.out','w')

    rvComm=' '.join(args)

    if options.verbose:
        print "Starting thread with command:\n%s" % rvComm
    current = memit(rvComm, options)
    current.start()

    events=[]
    if options.verbose:
        print "Monitoring process %s" % current.pid
    while(current.isAlive()):
        os.system('sleep %f ' % options.sleep)

        if current.pid>0:
            cmd = 'ps -p %s -o pid,rss,vsize,time,cmd --no-headers' % current.pid
            output = commands.getoutput(cmd)
            m = re.match('\s+(\d+)\s+(\d+)\s+(\d+)\s+((\d+:){2}\d+)', output)
            if m:
                fout.write("%s\t%s\t%s\t%s\t" % (m.group(1),\
                                                 m.group(2),\
                                                 m.group(3),\
                                                 m.group(4)))
                if os.path.exists('checkMem.log'):
                    eventNum=-1
                    evs= os.popen('tail -10000 checkMem.log | grep "Begin processing the" | tail -1')
                    evsRes=evs.readline()
                    if 'Begin processing' in evsRes:
                        if len(evsRes.split())>3:
                            eventNum=int(evsRes.split()[3][:-2])
                    events.append(eventNum)
                else:
                    events.append(-1)
                fout.write(str(events[-1])+'\n')
            else:
                print 'Unable to monitor the job\n'
    if not current.exitcode == 0:
        sys.exit(1)


# Parse command line options.
op = OptionParser()
op.add_option("-s", "--sleep", dest = "sleep",
              type = "float", action = "store", metavar = "SLEEP",
              default = 0.2, help = "Monitor the process every SLEEP seconds (could be a float).")

op.add_option("-v", "--verbose", dest = "verbose",
              action = "store_true", default = False,
              help = "Show verbose scan information")

options, args = op.parse_args()

if __name__ == '__main__' :
    main(options, args)
