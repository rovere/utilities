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


def getNumberOfGoodVertices(pv_h):
 good_vertices = 0
 for pv in range(pv_h.product().size()):
  if not pv_h.product()[pv].isFake() and pv_h.product()[pv].ndof() >=4:
   good_vertices += 1
 return good_vertices

def main(args):

    MAX_FILES_TO_PROCESS = 20
    f = TFile(args.output, "RECREATE")
    tracks_h = Handle("std::vector<reco::Track>")
    pv_h = Handle("std::vector<reco::Vertex>")
    hit_type = {0:'ok', 1:'missing', 2:'inactive', 3:'bad'}
    hit_category = {0:'track_hits', 1:'missing_inner_hits', 2:'missing_outer_hits'}
    det = {1:'PXB', 2:'PXF', 3:'TIB', 4:'TID', 5:'TOB', 6:'TEC'}
    subdet = {'PXB': {1:'Layer1', 2:'Layer2', 3:'Layer3'}, 'PXF':{1:'Disk1', 2:'Disk2'}, 'TIB':{1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4'}, 'TID':{1:'wheel1', 2:'wheel2', 3:'wheel3'}, 'TOB':{1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4', 5:'Layer5', 6:'Layer6'}, 'TEC':{1:'wheel1', 2:'wheel2', 3:'wheel3', 4:'wheel4', 5:'wheel5', 6:'wheel6', 7:'wheel7', 8:'wheel8', 9:'wheel9'}}

    histograms = {}
    histograms_barrel = {}
    histograms_endcap = {}
    for d in subdet.keys():
        for sd in subdet[d].keys():
            name = d+subdet[d][sd]
            histograms.setdefault(name, {}).setdefault(0, TH1F('Hits_ok_%s' % name, 'Hits_ok_%s' % name, 40, 0.5, 40.5)).Sumw2
            histograms.setdefault(name, {}).setdefault(1, TH1F('Hits_missing_%s' % name, 'Hits_missing_%s' % name, 40, 0.5, 40.5)).Sumw2
            histograms.setdefault(name, {}).setdefault(2, TH1F('Hits_inactive_%s' % name, 'Hits_inactive_%s' % name, 40, 0.5, 40.5)).Sumw2
            histograms.setdefault(name, {}).setdefault(3, TH1F('Hits_bad_%s' % name, 'Hits_bad_%s' % name, 40, 0.5, 40.5)).Sumw2
            histograms.setdefault(name, {}).setdefault(4, TH1F('Hits_ok_and_missing_%s' % name, 'Hits_ok_and_missing_%s' % name, 40, 0.5, 40.5)).Sumw2

            histograms_barrel.setdefault(name, {}).setdefault(0, TH1F('Hits_ok_%s_barrel' % name, 'Hits_ok_%s_barrel' % name, 40, 0.5, 40.5)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(1, TH1F('Hits_missing_%s_barrel' % name, 'Hits_missing_%s_barrel' % name, 40, 0.5, 40.5)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(2, TH1F('Hits_inactive_%s_barrel' % name, 'Hits_inactive_%s_barrel' % name, 40, 0.5, 40.5)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(3, TH1F('Hits_bad_%s_barrel' % name, 'Hits_bad_%s_barrel' % name, 40, 0.5, 40.5)).Sumw2
            histograms_barrel.setdefault(name, {}).setdefault(4, TH1F('Hits_ok_and_missing_%s_barrel' % name, 'Hits_ok_and_missing_%s_barrel' % name, 40, 0.5, 40.5)).Sumw2

            histograms_endcap.setdefault(name, {}).setdefault(0, TH1F('Hits_ok_%s_endcap' % name, 'Hits_ok_%s_endcap' % name, 40, 0.5, 40.5)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(1, TH1F('Hits_missing_%s_endcap' % name, 'Hits_missing_%s_endcap' % name, 40, 0.5, 40.5)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(2, TH1F('Hits_inactive_%s_endcap' % name, 'Hits_inactive_%s_endcap' % name, 40, 0.5, 40.5)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(3, TH1F('Hits_bad_%s_endcap' % name, 'Hits_bad_%s_endcap' % name, 40, 0.5, 40.5)).Sumw2
            histograms_endcap.setdefault(name, {}).setdefault(4, TH1F('Hits_ok_and_missing_%s_endcap' % name, 'Hits_ok_and_missing_%s_endcap' % name, 40, 0.5, 40.5)).Sumw2

    # DATA
    #events = Events("root://eoscms//store/data/Run2015C/SingleMuon/RECO/PromptReco-v1/000/254/790/00000/EA3E4890-224A-E511-83F5-02163E011F65.root")
    #events = Events("EA3E4890-224A-E511-83F5-02163E011F65.root")

    # MC 50 ns

    # events = Events("root://eoscms//store/relval/CMSSW_7_6_0_pre3/RelValTTbar_13/GEN-SIM-RECO/PU50ns_75X_mcRun2_startup_v2-v1/00000/B0821785-2A42-E511-B404-0025905A612A.root")

    # MC 25 ns

    files = []
    if args.input:
        files.append(args.input)
    elif args.eosdir:
        files.extend(map(lambda x: 'root://eoscms/'+ x, getFileListFromEOS(args.eosdir)) )
    else:
        print 'No input given, quitting'
        sys.exit(1)

    total_files = min(MAX_FILES_TO_PROCESS, len(files))
    analyzed_files = 0
    start_cumulative_time = time()
    start_time = start_cumulative_time
    end_time = start_cumulative_time
    for input_file in files:
        analyzed_files += 1
        if analyzed_files > MAX_FILES_TO_PROCESS:
            break
        print "\n", input_file
        events = Events(input_file)
        total_events = float(events.size())
        analized_events = 0.
        for e in range(events.size()):
         analized_events += 1.0
         if analized_events*100./total_events == 100:
             end_time = time()
         sys.stdout.write("\r -> %4.1f [%4.1f m] ETA: %4.1f m" % (analized_events*100./total_events,
                                                                  (end_time-start_time)/60.,
                                                                  (end_time-start_cumulative_time)/(60.*analyzed_files) * (total_files - analyzed_files)))
         start_time = end_time
         sys.stdout.flush()
        # if e > 2:
        #     break
         a = events.to(e)
         a = events.getByLabel("generalTracks", tracks_h)
         a = events.getByLabel("offlinePrimaryVertices", pv_h)
         good_vertices = getNumberOfGoodVertices(pv_h)
         if good_vertices < 1:
             continue
         for track in range(tracks_h.product().size()):
          t = tracks_h.product()[track]
          if t.pt() < 1.0 or t.dxy() > 0.1:
           continue
          hp = t.hitPattern()
          for category in hit_category.keys():
           if args.debug:
             print hit_category[category]
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
            if abs(t.eta()) < 1.4:
                if name in histograms_barrel.keys():
                    histograms_barrel[name][hit_type].Fill(good_vertices)
            else:
                if name in histograms_endcap.keys():
                    histograms_endcap[name][hit_type].Fill(good_vertices)

            if name in histograms.keys():
                    histograms[name][hit_type].Fill(good_vertices)
            if args.debug:
                print "%d) %s  %s, Type:%d" % (hit, d, sd, hp.getSide(pattern))
                print "V", hp.validHitFilter(pattern)
                print "M", hp.missingHitFilter(pattern)
                print "I", hp.inactiveHitFilter(pattern)
                print "B", hp.badHitFilter(pattern)

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

if __name__ == '__main__':
      parser = argparse.ArgumentParser(description='Quick Efficiency from HitPattern.',
                                       formatter_class=argparse.ArgumentDefaultsHelpFormatter)
      parser.add_argument('-i', '--input',
                          help='Input file to be used to extract information to produce the ntuple. Usually it must contain the RECO datatier. This option has the precedence on the -e/--eosdir one if both are specified.',
                          type=str,
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
      parser.add_argument('-d', '--debug',
                          help='Enable debug printpouts.',
                          default=False,
                          action = 'store_true')

      args = parser.parse_args()
      main(args)
