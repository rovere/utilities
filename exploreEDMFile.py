#!/usr/bin/env python

import os, sys, argparse
from struct import unpack
from autovars import *
from ObjectsNtuple import *

import idtodet
from collections import OrderedDict

qualities = OrderedDict([
#(  'UNDEFQUALITY',    -1),
(  'LOOSE',    0),
(  'TIGHT',    1),
(  'HIGHPURITY',    2),
(  'CONFIRMED',    3),
(  'GOODITERATIVE',    4),
(  'LOOSESETWITHPV',    5),
(  'HIGHPURITYSETWITHPV',    6),
(  'QUALITYSIZE',   7)
])

det = {1:'PXB',
       2:'PXF',
       3:'TIB',
       4:'TID',
       5:'TOB',
       6:'TEC'}
subdet = {'PXB': { 1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4'},
          'PXF': { 1:'Disk1',  2:'Disk2', 3:'Disk3'},
          'TIB': { 1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4'},
          'TID': { 1:'wheel1', 2:'wheel2', 3:'wheel3'},
          'TOB': { 1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4', 5:'Layer5', 6:'Layer6'},
          'TEC': { 1:'wheel1', 2:'wheel2', 3:'wheel3', 4:'wheel4', 5:'wheel5', 6:'wheel6', 7:'wheel7', 8:'wheel8', 9:'wheel9'}}


# Do not forget trailing '/'.
EOS_REPO = '/store/group/phys_tracking/rovere/JetHT22Jan/JetHT/crab_JetHT_legacyJan22/150223_172317/0000/'
# Grab it after some lookups throu type -a eoscms/eos
EOS_COMMAND = '/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select'
HEADER = "(           Idx  'ori'       eta        phi         pt  NVHits  NVPHits ndof       chi2  Algo-4   OriAlgo-4  HP?    LVHitLoc  stopR     key_idx)"
HEADER_VTX = "(  Chi2     ndof     normChi2     fake?   Valid?   NTrks      x            y            z          xE          yE           zE         index)"

def lastValidHitFromHP(hp):
  hit_category = 0 # Tracker hits
  last_valid_hit_location = ''
  try:
    for hit in range(0, hp.numberOfHits(hit_category)):
      pattern = hp.getHitPattern(hit_category, hit)
      valid = hp.validHitFilter(pattern)
      if valid:
        d = det[hp.getSubStructure(pattern)]
        sd = subdet[d][hp.getSubSubStructure(pattern)]
        last_valid_hit_location = d + '_' + sd
  except:
    return 'Invalid'
  return last_valid_hit_location

def printFullHP(hp):
  result = ''
  for hit_category in range(0,3):
#    hit_category = 0 # Tracker hits
    last_valid_hit_location = ''
#    try:
    for hit in range(0, hp.numberOfHits(hit_category)):
        pattern = hp.getHitPattern(hit_category, hit)
        valid = hp.validHitFilter(pattern)
        d = det[hp.getSubStructure(pattern)]
        sd = subdet[d][hp.getSubSubStructure(pattern)]
        hit_location = d + '_' + sd + '_Category_' + str(hit_category) + '_' + str(valid)
        result += hit_location
#    except:
#      return 'Invalid'
  return result

def fillStopReason(histo, hp, stopReason):
  hit_category = 0 # Tracker hits
  last_valid_hit_location = 0
  for hit in range(0, hp.numberOfHits(hit_category)):
    pattern = hp.getHitPattern(hit_category, hit)
    valid = hp.validHitFilter(pattern)
    if valid:
      d = hp.getSubStructure(pattern)
      sd = hp.getSubSubStructure(pattern)
      last_valid_hit_location = 10 * d + sd
  histo.Fill(last_valid_hit_location, stopReason)

def printPixelClusters(eventsRef, args):
  container_kind = "edmNew::DetSetVector<SiPixelCluster>"
  collection_label = args.pixelcluster if args.pixelcluster else "siPixelClusters"
  from DataFormats.FWLite import Handle, Events
  clustersRef = Handle(container_kind)
  label = collection_label
  for e in range(eventsRef.size()):
    a = eventsRef.to(e)
    a = eventsRef.getByLabel(label, clustersRef)
    print "Run: %7d, LS: %5d, Event: %14d\n" % (eventsRef.eventAuxiliary().run(),
                                                eventsRef.eventAuxiliary().luminosityBlock(),
                                                eventsRef.eventAuxiliary().event())
    if not clustersRef.isValid():
      print "Missing collection ", label, container_kind
      continue
    for det in clustersRef.product():
      for cluster in det:
        print cluster.adc()
  
def printSimTrackInformation(eventsRef, args):
#  printPixelClusters(eventsRef, args)
  container_kind = "std::vector<SimTrack>"
  collection_label = args.simtracks if args.simtracks else "g4SimHits"
  from DataFormats.FWLite import Handle, Events
  tracksRef = Handle(container_kind)
  label = collection_label
  for e in range(eventsRef.size()):
    a = eventsRef.to(e)
    a = eventsRef.getByLabel(label, tracksRef)
    print "Run: %7d, LS: %5d, Event: %14d\n" % (eventsRef.eventAuxiliary().run(),
                                                eventsRef.eventAuxiliary().luminosityBlock(),
                                                eventsRef.eventAuxiliary().event())
    if not tracksRef.isValid():
      print "Missing collection ", label, container_kind
      continue
    for i, track in enumerate(tracksRef.product()):
      print "%d] %d %f  %f %f" % (i,
                                  track.type(),
                                  track.momentum().eta(), track.momentum().phi(),
                                  track.momentum().pt())
  
  
def printTrackInformation(eventsRef,
                          args):
  container_kind = "std::vector<reco::Track>"
  collection_label = args.tracks if args.tracks else "ctfWithMaterialTracksP5"
  quality = args.quality if args.quality else 'highPurity'
  sort_index = args.sortIndex if args.sortIndex else 0
  dumpHits = args.dumpHits if args.dumpHits else -1
  selector = args.selector if args.selector else None
  mvavals = args.mvavals if args.mvavals else None
  outfile = None
  stopReason = None
  from DataFormats.FWLite import Handle, Events
  tracksRef = Handle(container_kind)
  label = collection_label
  print "Analyzing Tracks: %s of quality %s" % (collection_label, quality)
  stopReason = None
  if args.stopReason:
    from ROOT import TFile, TH2F
    outfile = TFile(args.stopReason[0], "RECREATE")
    stopReason = TH2F("Stop Reason vs Tracker Component",
                      "Stop Reason vs Tracker Component",
                      70, 0.5, 69.5,
                      256, -0.5, 255.5)
  for e in range(573, eventsRef.size()):
    a = eventsRef.to(e)
    a = eventsRef.getByLabel(label, tracksRef)
    print "Run: %7d, LS: %5d, Event: %14d\n" % (eventsRef.eventAuxiliary().run(),
                                                eventsRef.eventAuxiliary().luminosityBlock(),
                                                eventsRef.eventAuxiliary().event())
    print HEADER
    if not tracksRef.isValid():
      print "Missing collection ", label, container_kind
      continue
    tr = []
    dump_index = 0
    for track in tracksRef.product():
      keep_track = False
      if quality == 'ANY':
        keep_track = True
      else:
        if (track.quality(track.qualityByName(quality))) :
          keep_track = True
      if keep_track:
          hp = track.hitPattern()
          tr.append((10*int(100*track.eta())+track.phi(),
                     "ori",
                     track.eta(),
                     track.phi(),
                     track.pt(),
                     track.numberOfValidHits() ,
                     track.hitPattern().numberOfValidPixelHits(),
                     track.ndof(),
                     track.chi2(),
                     track.algo()-4,
                     track.originalAlgo()-4,
                     track.quality(track.qualityByName("highPurity")),
                     lastValidHitFromHP(hp),
                     int(unpack('@B', track.stopReason())[0]) if args.stopReason else 0,
                     dump_index,
                     printFullHP(hp)))
          if args.stopReason:
            fillStopReason(stopReason, hp, int(unpack('@B', track.stopReason())[0]))
      if dump_index == dumpHits:
        print "Dumping hits for track index: %d" % dumpHits
        te = track.extra().get()
        for h in range(0, te.recHitsSize()):
          print "\n\n *** Hit number %d ***" % h
          print " Hit linked to cluster [key]: %d" % te.recHit(h).get().cluster().key()
          print idtodet.id2det(int(te.recHit(h).get().rawId()))
      dump_index += 1

    if selector:
      selectorRef = Handle('edm::ValueMap<int>')
      mod, label = selector.split(':')
      eventsRef.getByLabel(mod, label, selectorRef)
      if selectorRef.isValid():
        selector = selectorRef.product()
        for i in range(0, tracksRef.product().size()):
          print "Track at: %d with qualityMask: %d and qual: %d" % (i,
                                                                    tracksRef.product()[i].qualityMask(),
                                                                    int(selector.get(i)))
          for q in qualities.keys():
            q_val = int(qualities[q])
            if int(selector.get(i)) > 0:
              print "Quality: %s, Value: %d" % ( q, (selector.get(i) & (1<<q_val))>>q_val)
            else:
              print "Quality: %s, Value: 'Undefined'" % q
      else:
        print "Supplied selector %s is not valid" % selector

    if mvavals:
      mvavalsRef = Handle('edm::ValueMap<float>')
      eventsRef.getByLabel(mvavals, 'MVAVals', mvavalsRef)
      if mvavalsRef.isValid():
        mvaval = mvavalsRef.product()
        for i in range(0, tracksRef.product().size()):
          print "Track at: %d with qualityMask: %d and MVA: %f" % (i,
                                                                   tracksRef.product()[i].qualityMask(),
                                                                   float(mvaval.get(i)))
      else:
        print "Supplied mvavals %s is not valid" % mvavals
          
    tr.sort(key=lambda tr: tr[sort_index])
    for t in tr:
      print "(%14.8f   %s %10.7f %10.7f %10.7f %7d %8d %4d %10.7f %7d %5d %10d %11s %5d %12d %40s)" % t
    print HEADER
  if args.stopReason:
    outfile.cd()
    stopReason.Write()
    outfile.Close()

def printVertexInformation(eventsRef,
                          container_kind = "std::vector<reco::Vertex>",
                          collection_label = "offlinePrimaryVertices"):
  from DataFormats.FWLite import Handle, Events
  verticesRef = Handle(container_kind)
  label = collection_label
  print "Analyzing Vertices: %s" % collection_label
  for e in range(eventsRef.size()):
    a = eventsRef.to(e)
    a = eventsRef.getByLabel(label, verticesRef)
    print "Run: %7d, LS: %5d, Event: %14d\n" % (eventsRef.eventAuxiliary().run(),
                                                eventsRef.eventAuxiliary().luminosityBlock(),
                                                eventsRef.eventAuxiliary().event())
    print HEADER_VTX
    if not verticesRef.isValid():
      print "Missing collection ", label, container_kind
      continue
    tr = []
    dump_index = 0
    for vertex in verticesRef.product():
      tr.append((vertex.chi2(),
                 vertex.ndof(),
                 vertex.normalizedChi2(),
                 vertex.isFake(),
                 vertex.isValid(),
                 vertex.tracksSize(),
                 vertex.x(),
                 vertex.y(),
                 vertex.z(),
                 vertex.xError(),
                 vertex.yError(),
                 vertex.zError(),
                 dump_index))
      dump_index += 1
    for t in tr:
      print "(%9.6f %9.6f %9.6f %5d %8d %8d %12.8f %12.8f %12.8f %12.8f %12.8f %12.8f %6d)" % t
    print HEADER_VTX


def plotDistributionOfTracks(eventsRef,
                            histo,
                            container_kind="std::vector<reco::Track>",
                            collection_label="generalTracks",
                            quality="highPurity"):
  tracksRef = Handle(container_kind)
  label = collection_label
  for e in range(eventsRef.size()):
    a = eventsRef.to(e)
    a = eventsRef.getByLabel(label, tracksRef)
    counter = 0
    for track in tracksRef.product():
      if track.quality(track.qualityByName(quality)):
        counter += 1
    histo.Fill(counter)

def getFileListFromDAS(query):
  import commands
  files = commands.getoutput(query).split('\n')
  return files

def getFileListFromEOS(eosdir):
  import commands
  input_files = commands.getoutput('%s ls %s' % (EOS_COMMAND, eosdir))
  input_files = input_files.split('\n')
  input_files = map(lambda x: '%s%s' %(eosdir, x), input_files)
  return input_files

def filterByRun(eventsRef, runNumber):
  return eventsRef.eventAuxiliary().run() == runNumber 

def bookAutoNtuple(name, title):
  t = TreeNumpy(name, title)
  event_vars.makeBranches(t, False)
  track_vars.makeBranchesVector(t, False)
  globalMuon_vars.makeBranchesVector(t, False)
  vertex_vars.makeBranchesVector(t, False)
  return t

def bookNtuple(name):
  t = TreeNumpy(name, name)
  t.var('run', int)
  t.var('lumi', int)
  t.var('event', int)
  t.var('numTracks', int)
  t.vector('track_pt', 'numTracks', 5000, float)
  t.vector('track_eta', 'numTracks', 5000, float)
  t.vector('track_phi', 'numTracks', 5000, float)
  t.vector('track_dxy', 'numTracks', 5000, float)
  t.vector('track_dz', 'numTracks', 5000, float)
  t.vector('track_ndof', 'numTracks', 5000, int)
  t.vector('track_chi2', 'numTracks', 5000, float)
  t.vector('track_algo', 'numTracks', 5000, int)
  t.vector('track_valid_sistrip_hits', 'numTracks', 5000, int)
  t.vector('track_valid_pixel_hits', 'numTracks', 5000, int)
  return t

def fillSingleTrackEntry(t, track, index):
  t.vFillWithIndex('track_pt', index, track.pt())
  t.vFillWithIndex('track_eta', index, track.eta())
  t.vFillWithIndex('track_phi', index, track.phi())
  t.vFillWithIndex('track_dxy', index, track.dxy())
  t.vFillWithIndex('track_dz', index, track.dz())
  t.vFillWithIndex('track_ndof', index, track.ndof())
  t.vFillWithIndex('track_chi2', index, track.chi2())
  t.vFillWithIndex('track_algo', index, track.algo()-4)
  t.vFillWithIndex('track_valid_sistrip_hits', index, track.hitPattern().numberOfValidStripHits())
  t.vFillWithIndex('track_valid_pixel_hits', index, track.hitPattern().numberOfValidPixelHits())

def trackNtuplizer(eventsRef,
                   t,
                   container_kind="std::vector<reco::Track>",
                   collection_label="generalTracks"):
  tracksRef = Handle(container_kind)
  muonsRef = Handle("std::vector<reco::Muon>")
  vertexRef = Handle("std::vector<reco::Vertex>")
  vertexLabel = "offlinePrimaryVertices"
  label = collection_label
  sip = ROOT.SignedImpactParameter()
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
    if not filterByRun(eventsRef, 208307):
      if skipped%10 == 0:
        sys.stdout.write('X')
      skipped += 1
      continue
    processed += 1
    a = eventsRef.getByLabel(label, tracksRef)
    a = eventsRef.getByLabel("muons", muonsRef)
    a = eventsRef.getByLabel(vertexLabel, vertexRef)
    # t.fill('run', eventsRef.eventAuxiliary().run())
    # t.fill('lumi', eventsRef.eventAuxiliary().luminosityBlock())
    # t.fill('event', eventsRef.eventAuxiliary().event())
#    t.fill('numTracks', len(tracksRef.product()))
#    counter = 0
#    for track in tracksRef.product():
#      fillSingleTrackEntry(t, track, counter)
#      counter += 1
    PVCollection = map(lambda x: vertexRef.product()[0], tracksRef.product())
    PVCollectionMuons = map(lambda x: vertexRef.product()[0], muonsRef.product())
    event_vars.fillBranches(t, eventsRef.eventAuxiliary(), False)
    track_vars.fillBranchesVector(t, map(lambda x, y: (x, y), tracksRef.product(), PVCollection), False)
    globalMuon_vars.fillBranchesVector(t, map(lambda x, y: (x, y), muonsRef.product(), PVCollectionMuons), False)
    vertex_vars.fillBranchesVector(t, vertexRef.product(), False)
    t.tree.Fill()
    t.reset()
  sys.stdout.write('\n')

def main(args):
  from DataFormats.FWLite import Events
  from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F
  from tree import TreeNumpy
  import ROOT
  filename = args.filename
  f = None
  h = None
  t = None
  if args.ntuplize:
    f = TFile("firstTupla.root", "RECREATE")
    h = TH1F("h_Tracks", "Tracks", 500, 0, 2500)
    t = bookAutoNtuple("Tracks", "TrackNtuple")
  if args.eosdir:
    for filename in getFileListFromEOS(args.eosdir):
      print "Dumping content from file %s" % filename
      eventsRef = Events("root://eoscms.cern.ch//%s" % filename)
      trackNtuplizer(eventsRef, t)
  do_digi = False
  quality = args.quality
  for filename in args.filename:
    print "Dumping from file: %s" % filename
    eventsRef = Events("%s" % filename)
    if args.simtracks:
      printSimTrackInformation(eventsRef, args)
    if args.tracks:
      printTrackInformation(eventsRef, args)
    if args.vertices:
      printVertexInformation(eventsRef,
                             collection_label = args.vertices)
    if args.ntuplize:
      trackNtuplizer(eventsRef, t)

      # for filename in getFileListFromDAS("das_client.py --limit=0 --query='file dataset=/JetHT/Run2012D-22Jan2013-v1/RECO run=208307'"):
      #   print "Dumping content from file %s" % filename
      #   eventsRef = Events("root://cmsxrootd.fnal.gov//%s" % filename)
      #   quality="highPurity"
      #   trackNtuplizer(eventsRef, t)
      #   # plotDistributionOfTracks(eventsRef, h, quality=quality)
  if args.ntuplize:
    h.SaveAs("TrackQuality%s.root" % quality)
    f.Write()
    f.Close()
  
def outdated():
  siClusterRef = Handle("edmNew::DetSetVector<SiStripCluster>")
  clusters_label = "siStripClusters"
  siStripDigiRef = Handle("edm::DetSetVector<SiStripDigi>")
  digi_label = "siStripDigis"

  #c = TCanvas("c", "c", 1024, 1024)
  #cosmic_pt = TH1F("Cosmic_pt", "Cosmic_pt", 20, 0., 10.)
  #cosmic_num_valid_hits = TH1F("Cosmic_num_valid_hits", "Cosmic_num_valid_hits", 20, 0., 10.)
  for e in range(eventsRef.size()):
    a = eventsRef.to(e)
  #  a = eventsRef.getByLabel(label, tracksRef)
    b = eventsRef.getByLabel(clusters_label, "", "RECO", siClusterRef)
    if do_digi:
      c = eventsRef.getByLabel(digi_label, "ZeroSuppressed", "RECO", siStripDigiRef)
      print "Event %d, Size of digi: %d, Size of SiStripClusters collection: %d" % (e, siStripDigiRef.product().size(), siClusterRef.product().dataSize())
    else:
      print "Event %d, Size of SiStripClusters collection: %d" % (e, siClusterRef.product().dataSize())


if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Easily explore the content of an edm file.')
  parser.add_argument('-f', '--filename',
                      default = None,
                      nargs = 1,
                      help = 'EDM File to use to extract information.',
                      type = str,
                      required=False)
  parser.add_argument('-e', '--eosdir',
                      default = None,
                      nargs = 1,
                      help = 'EOS directory whose entire content will be used as input. Will invalidate -f/--filename parameter.',
                      type = str,
                      required = False)
  parser.add_argument('-t', '--tracks',
                      nargs = '?',
                      help = 'Print track information for the specified collection label.',
                      type = str)
  parser.add_argument('-g', '--simtracks',
                      nargs = '?',
                      help = 'Print simtrack information for the specified collection label.',
                      type = str)
  parser.add_argument('-p', '--pixelcluster',
                      nargs = '?',
                      help = 'Print pixel cluster information for the specified collection label.',
                      type = str)
  parser.add_argument('-v', '--vertices',
                      nargs = '?',
                      help = 'Print vertex information for the specified collection label.',
                      type = str)
  parser.add_argument('-q', '--quality',
                      default = 'ANY',
                      nargs = '?',
                      help = 'Select tracks with the specified quality only. ANY means select all tracks in the collection.',
                      type = str)
  parser.add_argument('-s', '--sortIndex',
                      default = 0,
                      nargs = '?',
                      help = """Index of sorting paramter [only for tracks]:
                                0 = eta+phi,
                                1 =  ori/new,
                                2 = eta, 3 = phi, 4 = pt, 5 = numValidHits,
                                6 = numValidPixelHits, 7 = ndof, 8 = chi2,
                                9 = algo, 10 = quality""",
                      type = int)
  parser.add_argument('-d', '--dumpHits',
                      default = -1,
                      nargs = '?',
                      help = """Dump all rawId of the hits associated to the specified track index.""",
                      type = int)
  parser.add_argument('-k', '--selector',
                      default = None,
                      nargs = '?',
                      help = 'Print quality information related to the specified selector. The input must be in the format module:label, e.g. initialStepSelector:initialStepLoose',
                      type = str)

  parser.add_argument('-m', '--mvavals',
                      default = None,
                      nargs = '?',
                      help = 'Print MVA classifier information related to the specified selector. The input must be the module label of the selector.',
                      type = str)

  parser.add_argument('-n', '--ntuplize',
                      default = False,
                      help = 'Run the Track Ntuplizer.',
                      action = 'store_true')

  parser.add_argument('-r', '--stopReason',
                      default = None,
                      nargs = 1,
                      help = 'Histogram the distribution of the stop Reason for the selected tracks. Save the results in the filename specified.',
                      type = str,
                      required = False)

  args = parser.parse_args()
  if args.filename:
    main(args)
