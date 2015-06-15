#!/usr/bin/env python

import os, sys
from eos_utils import *
from das_utils import *
from autovars import *
from ObjectsNtuple import *
import argparse

# Do not forget trailing '/'.
#EOS_REPO = '/store/group/phys_tracking/rovere/JetHT22Jan/JetHT/crab_JetHT_legacyJan22/150223_172317/0000/'
EOS_REPO = '/store/relval/CMSSW_7_4_0_pre8/RelValSingleMuPt10_UP15/GEN-SIM-RECO/MCRUN2_74_V7-v1/00000/'


def filterByRun(eventsRef, runNumber):
  return eventsRef.eventAuxiliary().run() == runNumber 

def bookAutoNtuple(name, title, args):
  from tree import TreeNumpy
  t = TreeNumpy(name, title)
  event_vars.makeBranches(t, False)
  if args.tracks:
    track_vars.makeBranchesVector(t, False)
  if args.muons:
    globalMuon_vars.makeBranchesVector(t, False)
  if args.vertices:
    vertex_vars.makeBranchesVector(t, False)
  if args.displacedV:
    displaced_vertex_vars.makeBranchesVector(t, False)
  return t

def trackNtuplizer(eventsRef,
                   t,
                   container_kind="std::vector<reco::Track>",
                   collection_label="generalTracks"):
  from DataFormats.FWLite import Handle, Events
  tracksRef = Handle(container_kind)
  muonsRef = Handle("std::vector<reco::Muon>")
  vertexRef = Handle("std::vector<reco::Vertex>")
  vertexLabel = "offlinePrimaryVertices"
  displaced_vertices_Ref = Handle("vector<reco::PFDisplacedVertex>")
  displaced_vertices_label = "particleFlowDisplacedVertex"
  label = collection_label
#  sip = ROOT.SignedImpactParameter()
  print "Analyzing Tracks: %s" % collection_label
  processed = 0
  skipped = 0
  sys.stdout.write('\n')
  total_events = float(eventsRef.size())
  for e in range(eventsRef.size()):
    if processed%10 == 0:
      sys.stdout.write("\r%f%%" % ((processed/total_events)*100.))
      sys.stdout.flush()
    a = eventsRef.to(e)
    processed += 1
    a = eventsRef.getByLabel(label, tracksRef)
    a = eventsRef.getByLabel("muons", muonsRef)
    a = eventsRef.getByLabel(vertexLabel, vertexRef)
    a = eventsRef.getByLabel(displaced_vertices_label, displaced_vertices_Ref)
    PVCollection = map(lambda x: vertexRef.product()[0], tracksRef.product())
    PVCollectionMuons = map(lambda x: vertexRef.product()[0], muonsRef.product())
    event_vars.fillBranches(t, eventsRef.eventAuxiliary(), False)
    if args.tracks:
      track_vars.fillBranchesVector(t, tracksRef.product(), False)
    if args.muons:
      muon_args = map(lambda x: (x.innerTrack() if x.isTrackerMuon() else x.bestTrack() , x), muonsRef.product())
      globalMuon_vars.fillBranchesVector(t, muon_args, False)
    if args.vertices:
      vertex_vars.fillBranchesVector(t, vertexRef.product(), False)
    if args.displacedV:
      displaced_vertex_vars.fillBranchesVector(t, displaced_vertices_Ref.product(), False)
    t.tree.Fill()
    t.reset()
  sys.stdout.write('\n')

def main(args):
  from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F
  import ROOT
  from DataFormats.FWLite import Handle, Events
  from tree import TreeNumpy
  f = TFile(args.output, "RECREATE")
  t = bookAutoNtuple("Tracks", "TrackNtuple", args)
  filename = ''
  if args.input and os.path.exists(args.input):
    eventsRef = Events("%s" % args.input)
    trackNtuplizer(eventsRef, t)
  elif args.eosdir:
    total_files = len(getFileListFromEOS(args.eosdir))
    counter = 1
    for filename in getFileListFromEOS(args.eosdir):
      print "Dumping content from file %s [%d/%d]" % (filename, counter, total_files)
      counter += 1
      if counter >= 35:
        break
      eventsRef = Events("root://eoscms.cern.ch//%s" % filename)
      trackNtuplizer(eventsRef, t)
  f.Write()
  f.Close()
  
if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Quick Ntuplizer for tracks.',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('-i', '--input',
                      help='Input file to be used to extract information to produce the ntuple. Usually it must contain the RECO datatier. This option has the precedence on the -e/--eosdir one if both are specified.',
                      type=str,
                      required=False)
  parser.add_argument('-e', '--eosdir',
                      help='Directory on EOS to scan to look for input files. Usually it must contain RECO datatier.',
                      type=str,
                      required=False)
  parser.add_argument('-t', '--tracks',
                      help='Create tree for tracks.',
                      action='store_true',
                      required=False)
  parser.add_argument('-m', '--muons',
                      help='Create tree for muons.',
                      action='store_true',
                      required=False)
  parser.add_argument('-v', '--vertices',
                      help='Create tree for vertices.',
                      action='store_true',
                      required=False)
  parser.add_argument('-d', '--displacedV',
                      help='Create tree for displaced vertices (from PF).',
                      action='store_true',
                      required=False)
  parser.add_argument('-o', '--output',
                      help='Output file to be used to save the ntuple.',
                      default='trackNtuple.root',
                      type=str,
                      required=True)
  args = parser.parse_args()
  main(args)
