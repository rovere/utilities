#!/usr/bin/env python

import os, sys
# Pure trick to start ROOT in batch mode, pass this only option to it
# and the rest of the command line options to this code.
oldargv = sys.argv[:]
sys.argv = [ '-b-' ]
import ROOT
ROOT.gROOT.SetBatch(True)
sys.argv = oldargv

from eos_utils import *
from das_utils import *
from autovars import *
from ObjectsNtuple import *
import argparse
from threading import Thread, Lock, currentThread
import re

# Do not forget trailing '/'.
#EOS_REPO = '/store/group/phys_tracking/rovere/JetHT22Jan/JetHT/crab_JetHT_legacyJan22/150223_172317/0000/'
EOS_REPO = '/store/relval/CMSSW_7_4_0_pre8/RelValSingleMuPt10_UP15/GEN-SIM-RECO/MCRUN2_74_V7-v1/00000/'

log_lock = Lock()
msgs = []

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

def locked_method(method):
  """Method decorator. Requires a lock object at self._lock"""
  def newmethod(self, *args, **kwargs):
    with log_lock:
      return method(self, *args, **kwargs)
  return newmethod

@locked_method
def logme(msg, index):
  if index < len(msgs):
    msgs[index] = msg
  else:
    msgs.insert(index, msg)
  full_msg = ''
  for m in msgs:
    full_msg += m
  sys.stdout.write("\r" + full_msg)
  sys.stdout.flush()

def trackNtuplizer(eventsRef,
                   t,
                   container_kind="std::vector<reco::Track>",
                   collection_label="generalTracks",
                   thread_id = 1):
  from DataFormats.FWLite import Handle, Events
  tracksRef = Handle(container_kind)
  muonsRef = Handle("std::vector<reco::Muon>")
  vertexRef = Handle("std::vector<reco::Vertex>")
  vertexLabel = "offlinePrimaryVertices"
  displaced_vertices_Ref = Handle("vector<reco::PFDisplacedVertex>")
  displaced_vertices_label = "particleFlowDisplacedVertex"
  label = collection_label
#  sip = ROOT.SignedImpactParameter()
#  print "Analyzing Tracks: %s" % collection_label
  processed = 0
  skipped = 0
  sys.stdout.write('\n')
  total_events = float(eventsRef.size())
  accepted_events = 0
  for e in range(eventsRef.size()):
    if processed%10 == 0:
      if args.selectHLTPath:
        logme("%3.0f%% acc:%4.3f%% | " % ((processed/total_events)*100.,
                                          (accepted_events/total_events)*100.
                                          ), thread_id)
        # sys.stdout.write("\r%3.2f%% accepted: %3.2f%%" % ((processed/total_events)*100.,
        #                                                   (accepted_events/total_events)*100.
        #                                                   ))
        # sys.stdout.flush()
      else:
        logme("%3.0f%% | " % ((processed/total_events)*100.), thread_id)
        # sys.stdout.write("\r%f%%" % ((processed/total_events)*100.))
        # sys.stdout.flush()
    a = eventsRef.to(e)
    processed += 1
    if args.selectHLTPath:
      if not checkTriggerSelection(eventsRef, args):
        continue
      else:
        accepted_events += 1
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

def checkTriggerSelection(eventsRef, args):
  from DataFormats.FWLite import Handle, Events
  triggerBits, triggerBitLabel = Handle("edm::TriggerResults"), ("TriggerResults","","HLT")
  eventsRef.getByLabel(triggerBitLabel, triggerBits)

  success = False
  names = eventsRef.object().triggerNames(triggerBits.product())
  for i in xrange(triggerBits.product().size()):
    for path in args.selectHLTPath.split(','):
      if re.match(path, names.triggerName(i)):
        success = success | (True if triggerBits.product().accept(i) else False)
        # No need to test all the paths, since they are in OR: a
        # single True is enough to stop the loop.
        if success:
          return success
  return success

def printTriggers(eventsRef):
  from DataFormats.FWLite import Handle, Events
  triggerBits, triggerBitLabel = Handle("edm::TriggerResults"), ("TriggerResults","","HLT")
  for iev, event in enumerate(eventsRef):
    eventsRef.getByLabel(triggerBitLabel, triggerBits)

    print "\nEvent %d: run %6d, lumi %4d, event %12d" % (iev,event.eventAuxiliary().run(), event.eventAuxiliary().luminosityBlock(),event.eventAuxiliary().event())
    print "\n === TRIGGER PATHS ==="
    names = event.object().triggerNames(triggerBits.product())
    for i in xrange(triggerBits.product().size()):
      print "Trigger ", names.triggerName(i),  ": ", ("PASS" if triggerBits.product().accept(i) else "fail (or not run)")
    if iev > 10: break

class ProcessOneEOSDirectory(Thread):
  def __init__(self, eos_path, args):
    Thread.__init__(self)
    self.eos_path_ = eos_path
    self.args_ = args

  def run(self):
    from DataFormats.FWLite import Events
    from ROOT import TFile
    from hashlib import sha256
    thread_id = int(currentThread().getName().replace('Thread-', '')) - 1
    counter = 1
    f = TFile(args.output.replace(".root", "_%s.root" % sha256(self.eos_path_).hexdigest()[0:9]), "RECREATE")
    t = bookAutoNtuple("Tracks", "TrackNtuple", args)
    total_files = len(getFileListFromEOS(self.eos_path_))
    for filename in getFileListFromEOS(self.eos_path_):
      logme("   [%3d/%3d]    | " % (counter, total_files), thread_id)
      counter += 1
      # if counter >= 35:
      #   break
      eventsRef = Events("root://eoscms.cern.ch//%s" % filename)
      if self.args_.printTriggers:
        printTriggers(eventsRef)
      trackNtuplizer(eventsRef, t, thread_id=thread_id)
    f.Write()
    f.Close()


def main(args):
  from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F
  import ROOT
  from DataFormats.FWLite import Handle, Events
  from tree import TreeNumpy
  filename = ''
  if args.input and os.path.exists(args.input):
    f = TFile(args.output, "RECREATE")
    t = bookAutoNtuple("Tracks", "TrackNtuple", args)
    eventsRef = Events("%s" % args.input)
    if args.printTriggers:
      printTriggers(eventsRef)
    trackNtuplizer(eventsRef, t)
    f.Write()
    f.Close()
  elif args.eosdir:
    local_threads = []
    for current_eos_dir in args.eosdir.split(','):
      local_threads.append(ProcessOneEOSDirectory(current_eos_dir, args))
      local_threads[-1].start()
    for t in local_threads:
      t.join()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Quick Ntuplizer for tracks.',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('-i', '--input',
                      help='Input file to be used to extract information to produce the ntuple. Usually it must contain the RECO datatier. This option has the precedence on the -e/--eosdir one if both are specified.',
                      type=str,
                      required=False)
  parser.add_argument('-e', '--eosdir',
                      help='Directories (comma separated) on EOS to scan to look for input files. Usually it must contain RECO datatier.',
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
  parser.add_argument('-x', '--printTriggers',
                      help='Print the full list of HLT paths and their results for the first 10 events.',
                      action='store_true',
                      required=False)
  parser.add_argument('-s', '--selectHLTPath',
                      help='Only process events that satisfy the OR of the list of HLT paths passed to this option, comma-separated. RegExp are accepted.',
                      type=str,
                      required=False)
  parser.add_argument('-o', '--output',
                      help='Output file to be used to save the ntuple.',
                      default='trackNtuple.root',
                      type=str,
                      required=True)
  args = parser.parse_args()
  main(args)
