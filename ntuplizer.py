#!/usr/bin/env python

from DataFormats.FWLite import Handle, Events

from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F
import ROOT
import os, sys
from tree import TreeNumpy
from autovars import *
from ObjectsNtuple import *
from eos_utils import *
from das_utils import *

# Do not forget trailing '/'.
#EOS_REPO = '/store/group/phys_tracking/rovere/JetHT22Jan/JetHT/crab_JetHT_legacyJan22/150223_172317/0000/'
EOS_REPO = '/store/relval/CMSSW_7_4_0_pre8/RelValSingleMuPt10_UP15/GEN-SIM-RECO/MCRUN2_74_V7-v1/00000/'


def filterByRun(eventsRef, runNumber):
  return eventsRef.eventAuxiliary().run() == runNumber 

def bookAutoNtuple(name, title):
  t = TreeNumpy(name, title)
  event_vars.makeBranches(t, False)
  track_vars.makeBranchesVector(t, False)
  globalMuon_vars.makeBranchesVector(t, False)
  vertex_vars.makeBranchesVector(t, False)
  return t

def trackNtuplizer(eventsRef,
                   t,
                   container_kind="std::vector<reco::Track>",
                   collection_label="generalTracks"):
  tracksRef = Handle(container_kind)
  muonsRef = Handle("std::vector<reco::Muon>")
  vertexRef = Handle("std::vector<reco::Vertex>")
  vertexLabel = "offlinePrimaryVertices"
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
    PVCollection = map(lambda x: vertexRef.product()[0], tracksRef.product())
    PVCollectionMuons = map(lambda x: vertexRef.product()[0], muonsRef.product())
    event_vars.fillBranches(t, eventsRef.eventAuxiliary(), False)
    track_vars.fillBranchesVector(t, tracksRef.product(), False)
    muon_args = map(lambda x: (x.innerTrack() if x.isTrackerMuon() else x.bestTrack() , x), muonsRef.product())
    globalMuon_vars.fillBranchesVector(t, muon_args, False)
    vertex_vars.fillBranchesVector(t, vertexRef.product(), False)
    t.tree.Fill()
    t.reset()
  sys.stdout.write('\n')

def main():
  f = TFile("trackTuplaNewMaterial.root", "RECREATE")
  t = bookAutoNtuple("Tracks", "TrackNtuple")
  filename = ''
  if len(sys.argv) > 1:
    filename = sys.argv[1]
  if filename != '':
    eventsRef = Events("%s" % filename)
    trackNtuplizer(eventsRef, t)
  else:
    for filename in getFileListFromEOS(EOS_REPO):
      print "Dumping content from file %s" % filename
      eventsRef = Events("root://eoscms.cern.ch//%s" % filename)
      trackNtuplizer(eventsRef, t)
  f.Write()
  f.Close()
  
if __name__ == '__main__':
  main()
