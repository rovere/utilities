#!/usr/bin/env python
# Original Author:  Marco Rovere
# Created:  Tue Feb 9 10:06:02 CEST 2010
# $Id: $

import re
import sys, os
import FWCore.ParameterSet.Config as cms

pwd = os.getenv('PWD') +'/'
sys.path.append(pwd)
env = os.getenv('CMSSW_RELEASE_BASE')
if env is not None:
    print 'Working with release ', os.getenv('CMSSW_VERSION'), ' in area ', env
    print os.getcwd()
else:
    print 'You must set a proper CMSSW environment first. Quitting.'
    sys.exit(1)

if len(sys.argv) < 2:
    print 'Error.\nUsage py2tex python_config_file'
    sys.exit(1)
else:
    toload = sys.argv[1] #'production'
    toload = re.sub('\.py', '', toload)
    towrite = 'index.html'
print "Trying to load", toload
try:
    a = __import__(str(toload))
except:
    print 'Import Failed, quitting...'
    sys.exit(1)

# open latex output file
if not os.path.exists(pwd+'html'):
    os.mkdir(pwd+'html')
out = open('./html/'+towrite,'w')

options = cms.Options()

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
  li.Path       {font-style:bold;   color: #03C;}
  li.Sequence   {font-style:bold;   color: #09F;}
  li.EDProducer {font-style:italic; color: #a80000;}
  li.EDFilter   {font-style:italic; color: #F90;}
  li.EDAnalyzer {font-style:italic; color: #360;}
</style>
 </head>

 <body>
"""

def endDocument():
    return "</body>\n</html>\n"


def dumpProducerOrFilter(toEval, sec, sq):
    atype = str(type(eval(toEval)))
    atype = re.sub('[<\'>"]', '', atype)
    tmp = re.split('\.', atype)
    title = tmp.pop()
    shortTitle = re.sub('ED([a-zA-Z]).*', '\\1', title)
    toEv = toEval + '.dumpPython()'
    filename = eval(toEval + '._filename')
    filename = filename.replace(env+'/python/','')
    gg = eval(toEv)
    gr = re.search(title + '\s*\(\s*"(.*)"', gg)
    link = ''
    if gr:
        link = '<a href=http://cmslxr.fnal.gov/lxr/ident?i=' + gr.group(1) + '>' + gr.group(1) + '</a>\n'
    out.write('<li class=%s>%s %s, label <a href=%s.html>%s</a>, defined in %s</li>\n' %
              (title, title, link, sq, sq, filename))
#    out.write('<li>'+  title + ' ' + link + ', label <a href=' + sq + '.html>' + sq +'</a>, defined in ' + filename + '</li>\n')
    tmpout = open('./html/'+sq + '.html','w')
    tmpout.write(preamble())
    tmpout.write( '<pre>\n')
    cutAtColumn = 978
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


def dumpSequence(seq, sectionDepth):
#    out.write( seq, eval(seq), type(eval(seq)))
    aseq = eval(seq).dumpConfig('')
    aseq = re.sub('cms.SequencePlaceholder\("(.*?)"\)', '\\1', aseq)
    aseq = re.sub('[\(\)]', '', aseq)
    m = re.search('{(.*)}', aseq)
    if m:
        out.write('<ol>\n')
#        out.write( m.group(1))
        sqs = re.split('[,*+\&]',m.group(1))
        print 'dumpSequence', sqs
        for sq in sqs:
            toEval = 'a.process.'+sq
#            print sq, 'is of type', type(eval(toEval))
#            sq = re.sub('_', '\_', sq)
            sec = '\\'
            for i in range(0,sectionDepth):
                sec += 'sub'
            sec += 'section'
            try:
                if type(eval(toEval)) == cms.Sequence:
                    out.write('<li class=Sequence>Sequence %s</li>\n' % sq)
                    sectionDepth += 1
                    dumpSequence(toEval, sectionDepth)
                    sectionDepth -= 1
                    out.write('\n')
                else: # it is an EDProducer or an EDFilter (or even Looper??)
                    dumpProducerOrFilter(toEval, sec, sq)
            except:
                pass
        out.write('</ol>\n')



# Main starts here.

# Check if the supplied configuration file has a process defined in
# it. In case there is no process defined (e.g. when the file only
# contains paths and/or sequences), create a small fake configuraion
# file, with a DUMMY process and load the file under investigation on
# top of it.

try:
    print a.process.process
except:
    print 'No process defined in the supplied configuration file: creating a DUMMY one'
    cmsswBase = os.getenv('CMSSW_BASE')
    tmpFile = open('dummy.py','w')
    tmpFile.write("import FWCore.ParameterSet.Config as cms\n")
    tmpFile.write("process = cms.Process('FAKE')\n\n")
    pythonLibToLoad = (pwd + sys.argv[1]).replace(cmsswBase,'').replace('/src/','').replace('/', '.').replace('.python','').replace('.py','')
    tmpFile.write("process.load('" + pythonLibToLoad + "')")
    tmpFile.close()
    a = __import__('dummy')
    os.unlink('dummy.py')
    os.unlink('dummy.pyc')

out.write(preamble())
out.write( '<h1>Paths</h1>\n')
for k in a.process.paths.keys():
    apath =  a.process.paths[k].dumpConfig(options)
    apath = re.sub('cms.SequencePlaceholder\("(.*?)"\)', '\\1', apath)
    kk = k
    out.write( '<ol><li class=Path>Path %s</li>\n' % kk)
    m = re.search('{(.*)}', apath)
    if m:
        sqs = re.split('&|,',m.group(1))
        for sq in sqs:
            if len(sq) > 0:
                toEval = 'a.process.'+sq
                if type(eval(toEval)) == cms.Sequence:
                    out.write( '<ol><li class=Sequence>Sequence %s</li>\n' % sq)
                    dumpSequence(toEval, 2)
                    out.write('</ol>')
                else :
                    dumpProducerOrFilter(toEval, '\subsection', sq)
    out.write( '</ol>\n')

out.write( '<h1>End Paths</h1>\n')
for k in a.process.endpaths.keys():
    apath =  a.process.endpaths[k].dumpConfig(options)
    apath = re.sub('cms.SequencePlaceholder\("(.*?)"\)', '\\1', apath)
#    kk = re.sub('_', '\_', k)
    kk = k
    out.write( '<ol><li>Path ' + kk + '</li>\n')
    m = re.search('{(.*)}', apath)
    if m:
#        print m.group(1)
        sqs = re.split('&|,',m.group(1))
        for sq in sqs:
            toEval = 'a.process.'+sq
#            print toEval, eval(toEval), type(eval(toEval))
#            sq = re.sub('_', '\_', sq)
            if type(eval(toEval)) == cms.Sequence:
                out.write( '<ol><li>Sequence ' + sq + '</li>\n')
#                 out.write( '\index{' + sq + '}\n')
#                 out.write( '\index{Sequence!' + sq + '}\n')
                dumpSequence(toEval, 2)
                out.write('</ol>')
            else :
                dumpProducerOrFilter(toEval, '\subsection', sq)
    out.write('</ol>\n')

if 0:
    out.write( '<ol>Sequences\n')
    for k in a.process.sequences.keys():
        apath =  a.process.sequences[k].dumpConfig(options)
        #    apath = re.sub('cms.SequencePlaceholder\("(.*?)"\)', '\\1', apath)
        apath = re.sub('[\(\)]', '', apath)
#        kk = re.sub('_', '\_', k)
        kk = k
        out.write( '<li>Sequence ' + kk + '</li>\n')
        m = re.search('{(.*)}', apath)
        if m:
            sqs = re.split('&|,',m.group(1))
            print 'Sequences Chapter', sqs
            for sq in sqs:
                toEval = 'a.process.'+sq
                #            print toEval, eval(toEval), type(eval(toEval))
#                sq = re.sub('_', '\_', sq)
                try:
                    if type(eval(toEval)) == cms.Sequence:
                        out.write( '<li>Sequence ' + sq + '</li>\n')
#                         out.write( '\index{' + sq + '}\n')
#                         out.write( '\index{Sequence!' + sq + '}\n')
                        dumpSequence(toEval, 2)
                    else :
                        dumpProducerOrFilter(toEval, '\subsection', sq)
                except:
                    pass
    out.write( '</ol>\n')

sys.exit(0)
out.write( '<h1>ES_Sources</h1>\n')
for k in a.process.es_sources.keys():
#    kk = re.sub('_', '\_', k)
    kk = k
    gg = a.process.es_sources[k].dumpPython()
    gr = re.search('ESSource\s*\(\s*"(.*)"', gg)
    link = ''
    if gr:
        link = '<a href=http://cmslxr.fnal.gov/lxr/ident?i=' + gr.group(1) + '>' + gr.group(1) + '</a>\n'
    out.write( '<ol><li>' + kk + ' ' +  link +'</li>\n')
#     out.write( '\index{' + kk + '}\n')
#     out.write( '\index{ESSources!' + kk + '}\n')
    out.write( '<pre>\n')
    out.write( gg)
    out.write( '</pre>\n')
    out.write( '</ol>\n')

out.write( '<h1>ES_Producers</h1>\n')
for k in a.process.es_producers.keys():
#    kk = re.sub('_', '\_', k)
    kk = k
#     out.write( '\index{' + kk + '}\n')
#     out.write( '\index{ESProducers!' + kk + '}\n')
    gg = a.process.es_producers[k].dumpPython()
    gr = re.search('ESProducer\s*\(\s*"(.*)"', gg)
    link = ''
    if gr:
        link =  '<a href=http://cmslxr.fnal.gov/lxr/ident?i=' + gr.group(1) + '>' + gr.group(1) + '</a>\n'
    out.write( '<ol><li>' + kk + ' ' + link + '</li>\n')
    out.write( '<pre>\n')
    out.write( gg)
    out.write( '</pre>\n')
    out.write( '</ol>\n')

out.write( '<h1>ES_Prefers</h1>\n')
for k in a.process.es_prefers.keys():
#    kk = re.sub('_', '\_', k)
    kk = k
    out.write( '<ol><li>' + kk + '</li>\n')
#     out.write( '\index{' + kk + '}\n')
#     out.write( '\index{ESPrefers!' + kk + '}\n')
    out.write( '<pre>\n')
    gg = a.process.es_prefers[k].dumpPython()
    out.write( gg)
    out.write( '</pre>\n')
    out.write( '</ol>\n')

out.write( '<h1>Output Modules</h1>\n')
for k in a.process.outputModules.keys():
#    kk = re.sub('_', '\_', k)
    kk = k
    out.write( '<ol><li>' + kk + '</li>\n')
#     out.write( '\index{' + kk + '}\n')
#     out.write( '\index{OutputModule!' + kk + '}\n')
    out.write( '<pre>\n')
    gg = a.process.outputModules[k].dumpPython()
    out.write( gg)
    out.write( '</pre>\n')
    out.write( '</ol>\n')



out.write(endDocument())
