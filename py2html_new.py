#!/usr/bin/env python
# Original Author:  Marco Rovere
#         Created:  Tue Feb 9 10:06:02 CEST 2010
#         Last Updated: Thu Mar 26 16:04:30 CET 2020

import re
import sys, os
import sqlite3
import FWCore.ParameterSet.Config as cms
import FWCore.ParameterSet
import locale
import argparse

locale.setlocale(locale.LC_ALL, 'en_US')
numLabel = 0

class Visitor:
    def __init__(self, out, process, steps, prefix, connection=None):
        self.out = out
        self.process_ = process
        self.prefix_ = prefix
        self.env = os.getenv('CMSSW_RELEASE_BASE')
        self.t = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.level_ = 0
        self.level = {}
        self.level[self.level_] = 0
        self.steps_ = steps
        self.conn = connection

    def reset(self):
        self.t = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

    def enter(self, value):
        if type(value) == cms.Sequence:
            # Few modules define 'label' as a property, hiding the callable label() method...
            if (value.hasLabel_() and callable(value.label_)):
                self.out.write('<ol><li class=sequence>Sequence %s</li>\n<ol>' % value.label_())
            else:
                self.out.write('<ol><li class=sequence>Sequence %s</li>\n<ol>' % '--w/o label found--')
            self.level_ +=1
            self.level[self.level_] = 0
        elif 'Task' in dir(cms) and type(value) == cms.Task:
            ## check for older versions where Task was not defined
            if type(value) == cms.Task:
                if (value.hasLabel_() and callable(value.label_)):
                    self.out.write('<ol><li class=task>Task %s</li>\n<ol>' % value.label_())
                else:
                    self.out.write('<ol><li class=task>Task %s</li>\n<ol>' % '--w/o label found--')
                self.level_ +=1
                self.level[self.level_] = 0
        else:
            if type(value) == cms.EDAnalyzer:
                self.out.write( '<li class="EDAnalyzer">EDAnalyzer ' )
            elif type(value) == cms.EDProducer:
                self.out.write( '<li class="EDProducer">EDProducer ' )
            elif type(value) == cms.EDFilter:
                self.out.write( '<li class="EDFilter">EDFilter ' )
            elif type(value).__base__ == cms.SwitchProducer:
                self.out.write( '<li class="SwitchProducer">SwitchProducer ' )
            mem = self.dumpProducerOrFilter(value)
            for i in range(len(mem)):
                self.t[i] += int(mem[i])
                self.level[self.level_] += int(mem[i])

    def write_output(self, value, task=False):
        if task == True:
            if type(value) == cms.Sequence or type(value) == cms.Task:
                if value.hasLabel_() and callable(value.label_):
                    self.out.write('<span style="color:#000000">(%s, %s, %s, %s, %s) %f [%f] - %s </span>' % (prettyInt(self.t[0]),\
                        prettyInt(self.t[1]),\
                        prettyInt(self.t[2]),\
                        prettyInt(self.t[3]),\
                        prettyInt(self.t[4]),\
                        (self.t[0]+self.t[1]+self.t[2]+self.t[3]+self.t[4])/1024./1024.,\
                        self.level[self.level_]/1024./1024.,\
                        value.label_()))

                else:
                    self.out.write('<span style="color:#000000">(%s, %s, %s, %s, %s) %f [%f] - %s </span>' % (prettyInt(self.t[0]),\
                        prettyInt(self.t[1]),\
                        prettyInt(self.t[2]),\
                        prettyInt(self.t[3]),\
                        prettyInt(self.t[4]),\
                        (self.t[0]+self.t[1]+self.t[2]+self.t[3]+self.t[4])/1024./1024.,\
                        self.level[self.level_]/1024./1024.,\
                        '--No label found--'))

                self.level_ -= 1
                if self.level_ > 0:
                    self.level[self.level_] += self.level[self.level_+1]
                    self.level[self.level_+1] = 0
                self.out.write( '</ol></ol>\n')
            else:
                self.out.write( '</li>\n')
        else:
            if type(value) == cms.Sequence:
                if value.hasLabel_() and callable(value.label_):
                    self.out.write('<span style="color:#000000">(%s, %s, %s, %s, %s) %f [%f] - %s </span>' % (prettyInt(self.t[0]),\
                        prettyInt(self.t[1]),\
                        prettyInt(self.t[2]),\
                        prettyInt(self.t[3]),\
                        prettyInt(self.t[4]),\
                        (self.t[0]+self.t[1]+self.t[2]+self.t[3]+self.t[4])/1024./1024.,\
                        self.level[self.level_]/1024./1024.,\
                        value.label_()))

                else:
                    self.out.write('<span style="color:#000000">(%s, %s, %s, %s, %s) %f [%f] - %s </span>' % (prettyInt(self.t[0]),\
                        prettyInt(self.t[1]),\
                        prettyInt(self.t[2]),\
                        prettyInt(self.t[3]),\
                        prettyInt(self.t[4]),\
                        (self.t[0]+self.t[1]+self.t[2]+self.t[3]+self.t[4])/1024./1024.,\
                        self.level[self.level_]/1024./1024.,\
                        '--No label found--'))

                self.level_ -= 1
                if self.level_ > 0:
                    self.level[self.level_] += self.level[self.level_+1]
                    self.level[self.level_+1] = 0
                self.out.write( '</ol></ol>\n')
            else:
                self.out.write( '</li>\n')

    def leave(self, value):
        if 'Task' in dir(cms):
            self.write_output(value, task=True)
        else:
            self.write_output(value, task=False)

    def fake(self):
        return 'Not_Available'

    def dumpProducerOrFilter(self, value):
        # That's as horrible as I could think of. In the case of TaskPlaceholders
        # I noticed that the real object to be dumped it the process._name registered
        # in the TaskPlaceholder itself.
        if isinstance(value, FWCore.ParameterSet.SequenceTypes.TaskPlaceholder):
            value = getattr(self.process_, value._name)

        global numLabel
        type_ = getattr(value, 'type_', self.fake)
        filename_ = getattr(value, '_filename', self.fake())
        lbl_ = getattr(value, 'label_', self.fake)
        label_ = "Unknown"
        try:
          label_ = lbl_()
        except:
          label_ += "%d" % numLabel
          numLabel += 1
        dumpConfig_ = getattr(value, 'dumpPython', self.fake)
        link = ''
        counter = 0
        t = {}
        for step in self.steps_:
          toCheck = step
          if toCheck == 'ctor':
            toCheck = type_()
          if self.conn != None:
            try:
              cur = self.conn.execute("select mainrows.cumulative_count, name from symbols inner join mainrows on mainrows.symbol_id = symbols.id where name like '%s::%s%%';" % (type_(),toCheck))
              for r in cur:
                t[counter] = int(r[0])
              if len(t) != counter+1:
                t[counter] = 0
            except:
              t[counter] = 0
          else:
              t[counter] = 0
          counter += 1
        stats = '<span style="color:#000000">(%s, %s, %s, %s, %s) %s </span>' % (prettyInt(t[0]), \
                                                                                 prettyInt(t[1]), \
                                                                                 prettyInt(t[2]), \
                                                                                 prettyInt(t[3]), \
                                                                                 prettyInt(t[4]), \
                                                                                 prettyFloat((t[0]+t[1]+t[2]+t[3]+t[4])/1024./1024.))
        link = '<a href=https://cmssdt.cern.ch/dxr/CMSSW/search?q={}&redirect=false&case=false&limit=77&offset=>{}</a>{}\n'.format(type_(), type_(), stats)
        self.out.write(link + ', label <a href=' + label_ + '.html>' + label_ +'</a>, defined in ' + filename_ + '</li>\n')
        tmpout = open(os.path.join(self.prefix_, 'html/', label_ + '.html'), 'w')
        tmpout.write(preamble())
        tmpout.write( '<pre>\n')
        lines = []
        gg = dumpConfig_()
        lines = gg.split('\n')
        self.printAndExpandRefs(lines, tmpout, '')
        tmpout.write( '<pre>\n')
        tmpout.write(endDocument())
        tmpout.close()
        return t

    def printAndExpandRefs(self, lines, tmpout, indent):
        cutAtColumn = 978
        for line in lines:
            refs = re.search("refToPSet_\s+=\s+.*'(.*?)'", line)
            blocks = len(line)/cutAtColumn + 1
            for i in range(0,blocks):
                tmpout.write('%s%s' % (indent, line[i*cutAtColumn:(i+1)*cutAtColumn]))
                if blocks > 1 and not (i == blocks):
                    tmpout.write('\\ \n')
                else:
                    tmpout.write('\n')
            if refs:
                indent = '  '.join((indent, ''))
                tmpout.write('%s----------------------------------------------------------\n' % indent)
                self.printAndExpandRefs(getattr(self.process_, refs.group(1)).dumpPython().split('\n'), tmpout, indent)
                tmpout.write('%s----------------------------------------------------------\n' % indent)
        indent = indent[:-2]

def prettyInt(val):
    return locale.format("%d", int(val), grouping=True).replace(',', "'")

def prettyFloat(val):
    return locale.format("%.2f", float(val), grouping=True).replace(',', "'")

def preamble():
    return """
<html>
 <head>
  <title>Config Browser</title>
  <style type="text/css">
  ol {
   font-family: Arial;
   font-size: 10pt;
   padding-left: 25px;
  }
  .sequence {
   font-weight: bold;
  }
  .task {
   font-weight: bold;
  }
  li.Path       {font-style:bold;   color: #03C;}
  li.Task       {font-style:bold;   color: #3465A4;}
  li.sequence   {font-style:bold;   color: #09F;}
  li.task       {font-style:bold;   color: #FF6666;}
  li.EDProducer {font-style:italic; color: #a80000;}
  li.EDFilter   {font-style:italic; color: #F90;}
  li.EDAnalyzer {font-style:italic; color: #360;}
  li.SwitchProducer {font-style:italic; color: #4e9a06;}
</style>
 </head>

 <body>
"""

def endDocument():
    return "</body>\n</html>\n"

def checkRel():
    env = os.getenv('CMSSW_RELEASE_BASE')
    if env is not None:
        print 'Working with release ', os.getenv('CMSSW_VERSION'), ' in area ', env
        print os.getcwd()
    else:
        print 'You must set a proper CMSSW environment first. Quitting.'
        sys.exit(1)

def dumpESProducer(value, out, steps, prefix, conn=None):
    type_ = getattr(value, 'type_', 'Not Available')
    filename_ = getattr(value, '_filename', 'Not Available')
    lbl_ = getattr(value, 'label_', 'Not Available')
    dumpConfig_ = getattr(value, 'dumpPython', 'Not Available')
    link = ''
    counter = 0
    t = {}
    for step in steps:
      toCheck = step
      if toCheck == 'ctor':
        toCheck = type_()
      if conn != None:
        try:
          cur = conn.execute("select mainrows.cumulative_count, name from symbols inner join mainrows on mainrows.symbol_id = symbols.id where name like '%s::%s%%';" % (type_(),toCheck))
          for r in cur:
            t[counter] = int(r[0])
          if len(t) != counter+1:
            t[counter] = 0
        except:
          t[counter] = 0
      else:
          t[counter] = 0
      counter += 1
    stats = '<span style="color:#000000">(%s, %s, %s, %s, %s) %s </span>' % (prettyInt(t[0]), \
                                         prettyInt(t[1]), \
                                         prettyInt(t[2]), \
                                         prettyInt(t[3]), \
                                         prettyInt(t[4]), \
                                         prettyFloat((t[0]+t[1]+t[2]+t[3]+t[4])/1024./1024.))
    link = '<a href=https://cmssdt.cern.ch/dxr/CMSSW/search?q={}&redirect=false&case=false&limit=77&offset=>{}</a>{}\n'.format(type_(), type_(), stats)
    out.write('<ol><li>'+link + ', label <a href=' + lbl_() + '.html>' + lbl_() +'</a>, defined in ' + filename_ + '</li></ol>\n')
    tmpout = open(os.path.join(prefix, 'html', lbl_() + '.html'), 'w')
    tmpout.write(preamble())
    tmpout.write( '<pre>\n')
    cutAtColumn = 978
    gg = dumpConfig_()
    for line in gg.split('\n'):
        blocks = len(line)/cutAtColumn + 1
        for i in range(0,blocks):
            tmpout.write('%s' % line[i*cutAtColumn:(i+1)*cutAtColumn])
            if blocks > 1 and not (i == blocks):
                tmpout.write('\\ \n')
            else:
                tmpout.write('\n')
    tmpout.write( '<pre>\n')
    tmpout.write(endDocument())
    tmpout.close()
    return t

# Main starts here.

# Check if the supplied configuration file has a process defined in
# it. In case there is no process defined (e.g. when the file only
# contains paths and/or sequences), create a small fake configuraion
# file, with a DUMMY process and load the file under investigation on
# top of it.

def main(args):
  towrite = 'index.html'

  if args.igprof_out != '':
      conn = sqlite3.connect(sys.argv[2])
  else:
      conn = None

  steps = ('ctor', 'beginJob', 'beginRun', 'beginLuminosityBlock', 'analyze')
  pwd = os.getenv('PWD') +'/'
  sys.path.append(pwd)
  checkRel()

  cmsProcess = None
  try:
      a = __import__(str(re.sub('\.py', '', args.input_cfg)))
  except:
      print 'Import Failed, quitting...'
      sys.exit(1)

  if not os.path.exists(os.path.join(args.output,'html')):
      os.makedirs(os.path.join(args.output,'html'))
  out = open(os.path.join(args.output, 'html/') + towrite,'w')

  try:
      print a.process.process
      cmsProcess = a.process
  except:
      print 'No process defined in the supplied configuration file: creating a DUMMY one'
      cmsswBase = os.getenv('CMSSW_BASE')
      tmpFile = open('dummy.py','w')
      tmpFile.write("import FWCore.ParameterSet.Config as cms\n")
      tmpFile.write("process = cms.Process('FAKE')\n\n")
      pythonLibToLoad = (pwd + args.input_cfg).replace(cmsswBase,'').replace('/src/','').replace('/', '.').replace('.python','').replace('.py','')
      tmpFile.write("process.load('" + pythonLibToLoad + "')")
      tmpFile.close()
      a = __import__('dummy')
      os.unlink('dummy.py')
      os.unlink('dummy.pyc')

  out.write(preamble())
  out.write( '<h1>Paths</h1><ol>\n')
  v = Visitor(out, cmsProcess, steps, args.output, conn)
  for k in cmsProcess.paths.keys():
      out.write('<li class="Path">Path %s</li>\n<ol>' % k)
      cmsProcess.paths[k].visit(v)
      v.reset()
      out.write('</ol>')

  out.write( '</ol><h1>End Paths</h1>\n')
  v.reset()

  for k in cmsProcess.endpaths.keys():
      out.write('<H2>EndPath %s</H2>\n' % k)
      cmsProcess.endpaths[k].visit(v)
      v.reset()

  out.write( '</ol><h1>End Paths</h1>\n')
  v.reset()

  out.write( '<h1>Tasks</h1><ol>\n')
  for k in cmsProcess.tasks.keys():
      out.write('<li class="Task">Task %s</li>\n<ol>' % k)
      cmsProcess.tasks[k].visit(v)
      v.reset()
      out.write('</ol>')
  out.write( '</ol><h1>End Tasks</h1>\n')
  v.reset()


  out.write( '<h1>ES Producers</h1>\n')
  for k in cmsProcess.es_producers_().keys():
      out.write('<H2>ESProducer %s</H2>\n' % k)
      dumpESProducer(cmsProcess.es_producers[k], out, steps, args.output, conn)

  out.write(endDocument())


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_cfg', required=True, default='', type=str, help='Input cfg to parse')
  parser.add_argument('-p', '--igprof_out', required=False, default='', type=str, help='IgProf output to parse')
  parser.add_argument('-o', '--output', required=True, default='./html', type=str, help='Output directory where to store the fully expanded, html-ize configuration')

  args = parser.parse_args()
  main(args)
