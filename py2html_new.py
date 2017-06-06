#!/usr/bin/env python
# Original Author:  Marco Rovere
#         Created:  Tue Feb 9 10:06:02 CEST 2010

import re
import sys, os
import sqlite3
import FWCore.ParameterSet.Config as cms
import locale
import argparse

locale.setlocale(locale.LC_ALL, 'en_US')
numLabel = 0

class Visitor:
    def __init__(self, out, process, steps, prefix, ignore_igprof):
        self.out = out
        self.process_ = process
        self.prefix_ = prefix
        self.ignore_igprof_ = ignore_igprof
        self.env = os.getenv('CMSSW_RELEASE_BASE')
        self.t = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}
        self.level_ = 0
        self.level = {}
        self.level[self.level_] = 0
        self.steps_ = steps

    def reset(self):
        self.t = {0: 0, 1: 0, 2: 0, 3: 0, 4: 0}

    def enter(self, value):
        if type(value) == cms.Sequence:
            if (value.hasLabel_()):
                self.out.write('<ol><li class=sequence>Sequence %s</li>\n' % value.label_())
            else:
                self.out.write('<ol><li class=sequence>Sequence %s</li>\n' % '--w/o label found--')
            self.level_ +=1
            self.level[self.level_] = 0
        elif type(value) == cms.Task:
            if (value.hasLabel_()):
                self.out.write('<ol><li class=task>Task %s</li>\n' % value.label_())
            else:
                self.out.write('<ol><li class=task>Task %s</li>\n' % '--w/o label found--')
            self.level_ +=1
            self.level[self.level_] = 0
        else:
            if type(value) == cms.EDAnalyzer:
                self.out.write( '<li class="EDAnalyzer">EDAnalyzer ' )
            elif type(value) == cms.EDProducer:
                self.out.write( '<li class="EDProducer">EDProducer ' )
            elif type(value) == cms.EDFilter:
                self.out.write( '<li class="EDFilter">EDFilter ' )
            mem = self.dumpProducerOrFilter(value)
            for i in range(len(mem)):
                self.t[i] += int(mem[i])
                self.level[self.level_] += int(mem[i])
    def leave(self, value):
        if type(value) == cms.Sequence or type(value) == cms.Task:
            if value.hasLabel_():
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
#            print self.level
            self.level_ -= 1
            if self.level_ > 0:
                self.level[self.level_] += self.level[self.level_+1]
                self.level[self.level_+1] = 0
            self.out.write( '</ol>\n')
        else:
            self.out.write( '</li>\n')

    def fake(self):
        return 'Not_Available'

    def dumpProducerOrFilter(self, value):
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
        dumpConfig_ = getattr(value, 'dumpConfig', self.fake)
        link = ''
        counter = 0
        t = {}
        for step in self.steps_:
          toCheck = step
          if toCheck == 'ctor':
            toCheck = type_()
          if not self.ignore_igprof_:
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
        link = '<a href=http://cmssdt.cern.ch/SDT/lxr/ident?_i=' + type_() + '&_remember=1>' + type_() + '</a> ' + stats + '\n'
        self.out.write(link + ', label <a href=' + label_ + '.html>' + label_ +'</a>, defined in ' + filename_ + '</li>\n')
        tmpout = open(os.path.join(self.prefix_, 'html/', label_ + '.html'), 'w')
        tmpout.write(preamble())
        tmpout.write( '<pre>\n')
        gg = dumpConfig_()
        self.printAndExpandRefs(gg.split('\n'), tmpout, '')
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
  li.sequence   {font-style:bold;   color: #09F;}
  li.task       {font-style:bold;   color: #FF6666;}
  li.EDProducer {font-style:italic; color: #a80000;}
  li.EDFilter   {font-style:italic; color: #F90;}
  li.EDAnalyzer {font-style:italic; color: #360;}
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

def dumpESProducer(value, out, steps, prefix, ignore_igprof):
    type_ = getattr(value, 'type_', 'Not Available')
    filename_ = getattr(value, '_filename', 'Not Available')
    lbl_ = getattr(value, 'label_', 'Not Available')
    dumpConfig_ = getattr(value, 'dumpConfig', 'Not Available')
    link = ''
    counter = 0
    t = {}
    for step in steps:
      toCheck = step
      if toCheck == 'ctor':
        toCheck = type_()
      if not ignore_igprof:
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
    link = '<a href=http://cmssdt.cern.ch/SDT/lxr/ident?_i=' + type_() + '&_remember=1>' + type_() + '</a> ' + stats + '\n'
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

  if not args.ignore_igprof:
      conn = sqlite3.connect(sys.argv[2])

  steps = ('ctor', 'beginJob', 'beginRun', 'beginLuminosityBlock', 'analyze')
  pwd = os.getenv('PWD') +'/'
  sys.path.append(pwd)
  checkRel()

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
  v = Visitor(out, a.process, steps, args.output, args.ignore_igprof)
  for k in a.process.paths.keys():
      out.write('<li class="Path">Path %s</li>\n' % k)
      a.process.paths[k].visit(v)
      v.reset()

  out.write( '</ol><h1>End Paths</h1>\n')
  v.reset()

  for k in a.process.endpaths.keys():
      out.write('<H2>EndPath %s</H2>\n' % k)
      a.process.endpaths[k].visit(v)
      v.reset()

  out.write( '<h1>ES Producers</h1>\n')
  for k in a.process.es_producers_().keys():
      out.write('<H2>ESProducer %s</H2>\n' % k)
      dumpESProducer(a.process.es_producers[k], out, steps, args.output, args.ignore_igprof)

  out.write(endDocument())


if __name__ == '__main__':
  parser = argparse.ArgumentParser()
  parser.add_argument('-i', '--input_cfg', required=True, default='', type=str, help='Input cfg to parse')
  parser.add_argument('-o', '--output', required=True, default='./html', type=str, help='Output directory where to store the fully expanded, html-ize configuration')
  parser.add_argument('--ignore_igprof', required=False, default=True, help='Ignore igprof results in assembling the expanded configuration.')

  args = parser.parse_args()
  main(args)
