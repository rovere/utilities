#!/usr/bin/env python

# Pure trick to start ROOT in batch mode, pass this only option to it
# and the rest of the command line options to this code.
import sys
oldargv = sys.argv[:]
sys.argv = [ '-b-' ]
from ROOT import TGraphAsymmErrors, TH1F, TFile, gROOT
gROOT.SetBatch(True)
sys.argv = oldargv

import argparse
from DataFormats.FWLite import Handle, Events
from eos_utils import *
from time import time
import re

class bcolors:
    MISSING_INSIDE = '\033[1;31m'
    MISSING_OTHER = '\033[1;32m'
    ENDC = '\033[0m'

def printPattern(hit, category, d, sd, hp, pattern):
    begin = ''
    if category == 0:
        begin = bcolors.MISSING_INSIDE if hp.missingHitFilter(pattern) else ''
    else:
        begin = bcolors.MISSING_OTHER if hp.missingHitFilter(pattern) else ''
    end   = bcolors.ENDC if begin else ''
    print begin + "%d)\t %10s  %10s, Type:%1d --> V %1d M %1d I %1d B %1d" % (hit, d, sd, hp.getSide(pattern),
                                                                              hp.validHitFilter(pattern), hp.missingHitFilter(pattern),
                                                                              hp.inactiveHitFilter(pattern), hp.badHitFilter(pattern)) + end
    
def getNumberOfGoodVertices(pv_h):
 good_vertices = 0
 for pv in range(pv_h.product().size()):
  if not pv_h.product()[pv].isFake() and pv_h.product()[pv].ndof() >=4:
   good_vertices += 1
 return good_vertices

def explicitRange(input_list):
    result = []
    for l in input_list:
        if re.match('\d+-\d+', l):
            result.extend([i for i in xrange(int(l.split('-')[0]),int(l.split('-')[-1]) + 1)])
        else:
            result.append(int(l))
    return result
    
def main(args):

    MAX_FILES_TO_PROCESS = args.maxfiles
    x_axis_definition = [40, 0.5, 40.5]
    if args.bxaxis:
        x_axis_definition = [4000, -0.5, 3999.5]
    numerical_lumi = []
    numerical_bn = []
    # In case the user specified LS using the range syntax X-Y, extend it in the form X, X+1, ..., Y.
    if args.lumi:
        numerical_lumi.extend(explicitRange(args.lumi))
    # Same range extension for the BX number
    if args.bn:
        numerical_bn.extend(explicitRange(args.bn))
    print "Selecting LS: ", numerical_lumi
    print "Selecting BN: ", numerical_bn

    f = TFile(args.output, "RECREATE")
    tracks_h = Handle("std::vector<reco::Track>")
    pv_h = Handle("std::vector<reco::Vertex>")
    hit_type = {0:'ok', 1:'missing', 2:'inactive', 3:'bad'}
    hit_category = {0:'track_hits',
                    1:'missing_inner_hits',
                    2:'missing_outer_hits'}

    det = {1:'PXB',
           2:'PXF',
           3:'TIB',
           4:'TID',
           5:'TOB',
           6:'TEC'}
    subdet = {'PXB': { 1:'Layer1', 2:'Layer2', 3:'Layer3'},
              'PXF': { 1:'Disk1',  2:'Disk2'},
              'TIB': { 1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4'},
              'TID': { 1:'wheel1', 2:'wheel2', 3:'wheel3'},
              'TOB': { 1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4', 5:'Layer5', 6:'Layer6'},
              'TEC': { 1:'wheel1', 2:'wheel2', 3:'wheel3', 4:'wheel4', 5:'wheel5', 6:'wheel6', 7:'wheel7', 8:'wheel8', 9:'wheel9'}}

    histograms = {}
    histograms_barrel = {}
    histograms_endcap = {}
    for d in subdet.keys():
        for sd in subdet[d].keys():
            name = d+subdet[d][sd]
            histograms.setdefault(name, {}).setdefault(0, TH1F('Hits_ok_%s' % name, 'Hits_ok_%s' % name, *x_axis_definition)).Sumw2
            histograms.setdefault(name, {}).setdefault(1, TH1F('Hits_missing_%s' % name, 'Hits_missing_%s' % name, *x_axis_definition)).Sumw2
            histograms.setdefault(name, {}).setdefault(2, TH1F('Hits_inactive_%s' % name, 'Hits_inactive_%s' % name, *x_axis_definition)).Sumw2
            histograms.setdefault(name, {}).setdefault(3, TH1F('Hits_bad_%s' % name, 'Hits_bad_%s' % name, *x_axis_definition)).Sumw2
            histograms.setdefault(name, {}).setdefault(4, TH1F('Hits_ok_and_missing_%s' % name, 'Hits_ok_and_missing_%s' % name, *x_axis_definition)).Sumw2

            histograms_barrel.setdefault(name, {}).setdefault(0, TH1F('Hits_ok_%s_barrel' % name, 'Hits_ok_%s_barrel' % name, *x_axis_definition)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(1, TH1F('Hits_missing_%s_barrel' % name, 'Hits_missing_%s_barrel' % name, *x_axis_definition)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(2, TH1F('Hits_inactive_%s_barrel' % name, 'Hits_inactive_%s_barrel' % name, *x_axis_definition)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(3, TH1F('Hits_bad_%s_barrel' % name, 'Hits_bad_%s_barrel' % name, *x_axis_definition)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(4, TH1F('Hits_ok_and_missing_%s_barrel' % name, 'Hits_ok_and_missing_%s_barrel' % name, *x_axis_definition)).Sumw2

            histograms_endcap.setdefault(name, {}).setdefault(0, TH1F('Hits_ok_%s_endcap' % name, 'Hits_ok_%s_endcap' % name, *x_axis_definition)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(1, TH1F('Hits_missing_%s_endcap' % name, 'Hits_missing_%s_endcap' % name, *x_axis_definition)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(2, TH1F('Hits_inactive_%s_endcap' % name, 'Hits_inactive_%s_endcap' % name, *x_axis_definition)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(3, TH1F('Hits_bad_%s_endcap' % name, 'Hits_bad_%s_endcap' % name, *x_axis_definition)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(4, TH1F('Hits_ok_and_missing_%s_endcap' % name, 'Hits_ok_and_missing_%s_endcap' % name, *x_axis_definition)).Sumw2

    files = []
    if args.input:
        files.extend(args.input)
    elif args.eosdir:
        files.extend(map(lambda x: 'root://eoscms/'+ x, getFileListFromEOS(args.eosdir)) )
    else:
        print 'No input given, quitting'
        sys.exit(1)

    total_files = 0
    if MAX_FILES_TO_PROCESS < 0:
        total_files = len(files)
    else:
        total_files = min(MAX_FILES_TO_PROCESS, len(files))
    analyzed_files = 0
    start_cumulative_time = time()
    start_time = start_cumulative_time
    end_time = start_cumulative_time
    file_count = -1
    for input_file in files:
        file_count += 1
        analyzed_files += 1
        if MAX_FILES_TO_PROCESS > 0 and analyzed_files > MAX_FILES_TO_PROCESS:
            break
        print "\n", input_file
        events = Events(input_file)
        total_events = float(events.size())
        analized_events = 0.
        for e in range(events.size()):
         analized_events += 1.0
         if analized_events*100./total_events == 100:
             end_time = time()
         if not args.debug:
             sys.stdout.write("\r %d/%d --> %4.1f [%4.1f m / %6f s] ETA: %4.1f m ==> LS: %d" % (file_count, total_files,
                                                                                                analized_events*100./total_events,
                                                                                                (end_time-start_time)/60.,(end_time-start_time),
                                                                                                (end_time-start_cumulative_time)/(60.*analyzed_files) * (total_files - analyzed_files),
                                                                                                events.eventAuxiliary().luminosityBlock()))
         start_time = end_time
         sys.stdout.flush()
         a = events.to(e)
         if args.lumi:
             if not events.eventAuxiliary().luminosityBlock() in numerical_lumi:
                 continue
         if args.bn  and not events.eventAuxiliary().bunchCrossing() in numerical_bn:
             continue
         a = events.getByLabel("generalTracks", tracks_h)
         a = events.getByLabel("offlinePrimaryVertices", pv_h)
         good_vertices = getNumberOfGoodVertices(pv_h)
         if good_vertices < 1:
             continue
         for track in range(tracks_h.product().size()):
          t = tracks_h.product()[track]
          if not t.quality(t.qualityByName("highPurity")):
              continue
          if t.pt() < 1.0 or t.dxy() > 0.1:
           continue
          hp = t.hitPattern()
          if args.debug:
              print "\n\n"
          for category in hit_category.keys():
           if args.debug:
             print hit_category[category], "pt, eta, phi, dxy, originalAlgo-4", t.pt(), t.eta(), t.phi(), t.dxy(), t.originalAlgo()-4
           for hit in range(0, hp.numberOfHits(category)):
            pattern = hp.getHitPattern(category, hit)
            valid = hp.validHitFilter(pattern)
            missing = hp.missingHitFilter(pattern)
            inactive = hp.inactiveHitFilter(pattern)
            bad = hp.badHitFilter(pattern)
            hit_type = -1
            if valid:
                hit_type = 0
            elif missing:
                hit_type = 1
            elif inactive:
                hit_type = 2
            elif bad:
                hit_type = 3
            d = det[hp.getSubStructure(pattern)]
            sd = subdet[d][hp.getSubSubStructure(pattern)]
            name = d+sd
            if args.overwrite:
                good_vertices = args.overwrite
            if abs(t.eta()) < 1.4:
                if name in histograms_barrel.keys():
                    histograms_barrel[name][hit_type].Fill(good_vertices)
            else:
                if name in histograms_endcap.keys():
                    histograms_endcap[name][hit_type].Fill(good_vertices)

            if name in histograms.keys():
                # If the user asked to compute the efficiency only for
                # the missing hits belonging to the traker_hits
                # category (0), then we are going to stop at the
                # last-but-one hit of the corresponding hit-pattern,
                # so that we are always guarenteed that another valid
                # hit is present. The last hit of the tracker_hit
                # category, in fact, cannot be of the missing type.
                if args.hitcategory and len(args.hitcategory) == 1 and args.hitcategory[0] == 0 and hit == hp.numberOfHits(category) - 1:
                    if not category in args.hitcategory:
                        continue
                    if args.debug:
                        print "Omitting this hit for hit-efficiency purposes"
                        printPattern(hit, category, d, sd, hp, pattern)
                    continue
                if hit_type != 1:
                    histograms[name][hit_type].Fill(good_vertices)
                else:
                    if args.hitcategory and not category in args.hitcategory:
                        continue
                    histograms[name][hit_type].Fill(good_vertices)
            if args.debug:
                printPattern(hit, category, d, sd, hp, pattern)
    f.cd()
    for kind in histograms.keys():
        histograms[kind][4].Add(histograms[kind][0]+histograms[kind][1])
        histograms.setdefault(kind, {}).setdefault(5, TGraphAsymmErrors(histograms[kind][0], histograms[kind][4])).Write()

        histograms_barrel[kind][4].Add(histograms_barrel[kind][0]+histograms_barrel[kind][1])
        histograms_barrel.setdefault(kind, {}).setdefault(5, TGraphAsymmErrors(histograms_barrel[kind][0], histograms_barrel[kind][4])).Write()

        histograms_endcap[kind][4].Add(histograms_endcap[kind][0]+histograms_endcap[kind][1])
        histograms_endcap.setdefault(kind, {}).setdefault(5, TGraphAsymmErrors(histograms_endcap[kind][0], histograms_endcap[kind][4])).Write()

    if args.debug:
        f.ls()
    f.Write()
    f.Close()

# Some sanity-checks about what the users want us to do.
def checkArgs(args):
    if args.bxaxis and not args.overwrite:
        raise ValueError('Error, you must configure the overwrite parameter together with the bxaxis option. Quitting.')

if __name__ == '__main__':
      parser = argparse.ArgumentParser(description='Quick Efficiency from HitPattern.',
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
      parser.add_argument('-i', '--input',
                          help='Input files to be used to extract information to produce the ntuple. Usually it must contain the RECO datatier. This option has the precedence on the -e/--eosdir one if both are specified.',
                          type=str,
                          nargs='+',
                          required=False)
      parser.add_argument('-e', '--eosdir',
                          help='Directory on EOS to scan to look for input files. Usually it must contain AOD/RECO datatier.',
                          type=str,
                          required=False)
      parser.add_argument('-o', '--output',
                          help='Output file to be used to save the ntuple.',
                          default='trackNtuple.root',
                          type=str,
                          required=True)
      parser.add_argument('-l', '--lumi',
                          help='Filter on the specified Lumisection. The filter must be supplied in the form of an array, with comma-separated values. Ranges of the form X-Y are also allowed.',
                          type=str,
                          nargs='+',
                          required=False)
      parser.add_argument('-b', '--bn',
                          help='Filter on the specified Bunch number(s). Number should be space-separated. Range notation (fully inclusive), is also supported.',
                          nargs='+',
                          type=str,
                          required=False)
      parser.add_argument('-d', '--debug',
                          help='Enable debug printpouts.',
                          default=False,
                          action = 'store_true')
      parser.add_argument('-m', '--maxfiles',
                          help='Maximum number of input files to be processed. -1 means all files, w/o limits.',
                          default=20,
                          type=int,
                          required=True)
      parser.add_argument('-c', '--hitcategory',
                          help='Hit categories that should be considered to fill the *MISSING* plots. 0: track_hits, 1: missing_inner_hits, 2: missing_outer_hits. Multiple selection is allowed: each category must be comma-separated.',
                          nargs='+',
                          type=int)
      parser.add_argument('-v', '--overwrite',
                          help='Overwrite the number of good reconstructed vertices(or, more generally, the X-Axis value), still requiring at least one good vertex in the event.',
                          type=int)
      parser.add_argument('-x', '--bxaxis',
                          help='Turn the X-Axis into BX and not number of vertices. It must be used together with the -v option, otherwise it makes no sense.',
                          default=False,
                          action = 'store_true')
      args = parser.parse_args()
      checkArgs(args)
      main(args)
