#!/usr/bin/env python


import argparse
import os, re
from math import sqrt

eventsRef = None # Events("/afs/cern.ch/work/r/rovere/TrackingPOG/RecoRun1vsRecoRun2/CMSSW_7_4_0_pre8/src/relVal_requests/step3RunIReco.root")
eventsNew = None # Events("/afs/cern.ch/work/r/rovere/TrackingPOG/RecoRun1vsRecoRun2/CMSSW_7_4_0_pre8/src/relVal_requests/step3.root")

tracksRef = None # Handle("std::vector<reco::Track>")
tracksNew = None # Handle("std::vector<reco::Track>")
label = None # "generalTracks"
DELTA_R_CUT = None # 0.01
DELTA_PT_OVER_PT_CUT = None # 0.1

variable2index = ["order", "sample", "eta", "phi", "pt", "hits", "phits", "ndof", "chi2", "algo", "originalAlgo", "quality", "run", "ls", "event"]
histos = {}

def match(a, b):
    eta = getIndexOf('eta')
    pt = getIndexOf('pt')
    phi = getIndexOf('phi')
    deltaR = sqrt(( (a[eta] - b[eta])**2 + (a[phi] - b[phi])**2))
    deltaPt_over_Pt =abs(a[pt]-b[pt])/a[pt]
#    print "DeltaR: %f, DeltaPt_over_Pt: %f" % (
#        deltaR,
#        deltaPt_over_Pt
#        )
    return (deltaR, deltaPt_over_Pt)

def getIndexOf(variable):
    return variable2index.index(variable)

def producePlots(histos, suffix):
    from ROOT import TCanvas
    c = TCanvas("c", "c", 1024, 1024)
    options = ''
    for h in histos.keys():
        if re.match('.*_vs_.*', h):
            options += 'BOX'
        histos[h].Draw(options)
        c.SaveAs("%s_%s.png" % (h, suffix))

def computeEfficiency(num, den, eff, computeFake=False):
    """
    This piece of code is intentionally copied from the
    DQMGenericClient, which is the source of efficiency computation in
    CMSSW, and we want to comply to it. It will take in input the 3
    histograms, which are, in order, the numerator, the denominator
    and the final efficiency plot. The very same function is also able
    to compute the fake rate if the boolean computeFake is passed as
    True.
    """
    for iBinX in range(1, den.GetNbinsX() + 1):
        for iBinY in range(1, den.GetNbinsY() + 1):
            for iBinZ in range(1, den.GetNbinsZ() + 1):
                globalBinNum = den.GetBin(iBinX, iBinY, iBinZ)
                numerVal = num.GetBinContent(globalBinNum)
                denomVal = den.GetBinContent(globalBinNum)
                effVal = 0
#                print numerVal, denomVal
                #fake eff is in use
                if computeFake:
                    effVal = (1 - numerVal / denomVal) if denomVal else 0
                else:
                    effVal = numerVal / denomVal if denomVal else 0
#                print effVal, 1-effVal, denomVal
                errVal = sqrt(effVal*(1-effVal)/denomVal) if (denomVal != 0 and (effVal <=1)) else 0
                eff.SetBinContent(globalBinNum, effVal)
                eff.SetBinError(globalBinNum, errVal)

def compareTwoReco(reference, new, histos, debug=1):
    """
    In this routine the reference samples has to be treated as if it
    were Generator level information, while the new one has to be
    thought of as the reconstruction level quantity. Efficiencies and
    fake rates are computed according to the usual rules: the
    efficiency is the ratio between generator-level quantities of
    matched objects with respect to all generator-level entries, while
    the fake rate is computed as 1 - the efficiency.
    """

    # Tracks with index False are the ones that have been matched to the reference track collection
    new_valid = [True for i in new]

    # Tracks with index False are the ones that have been matched to the comparison track collection
    original_valid = [True for i in reference]
    pt = getIndexOf("pt")
    eta = getIndexOf("eta")
    phi = getIndexOf("phi")
    hits = getIndexOf("hits")
    algo = getIndexOf("algo")
    orialgo = getIndexOf("originalAlgo")
    run = getIndexOf("run")
    ls = getIndexOf("ls")
    event_number = getIndexOf("event")
    print " ".join("%10s" % k for k in variable2index)
    for original_index, original in enumerate(reference):
        # Fill in cumulative plots for the reference sample first
        histos['reference_hits_vs_algo'].Fill(original[algo], original[hits])
        histos['reference_hits_vs_orialgo'].Fill(original[orialgo], original[hits])
        histos['reference_hits_vs_pt'].Fill(original[pt], original[hits])
        histos['den'].Fill(original[pt])
        histos['den_eta'].Fill(original[eta])
        histos['den_phi'].Fill(original[phi])
        histos['den_hits'].Fill(original[hits])
        histos['den_algo'].Fill(original[algo])
        histos['den_orialgo'].Fill(original[orialgo])

        # Now start to look for a matching track in the comparison track collection
        window_depth = 400 # elements to span to look for best candidate
        iBest, bestDeltaRMatch, bestDeltaPt_over_PtMatch = -1, 100, 100
        if debug >=2:
            print original
        for i,j in enumerate(new):
            if new_valid[i] == True:
                if debug >=2:
                    print "  ", i, j
                if window_depth == 0:
                    break
                dr, dPt_over_pt = match(original, j)
                if dr < bestDeltaRMatch and dPt_over_pt < DELTA_PT_OVER_PT_CUT:
                    iBest, bestDeltaRMatch, bestDeltaPt_over_PtMatch = i, dr, dPt_over_pt
                if debug >=2:
                    print "  ", window_depth, iBest, bestDeltaRMatch, dr, bestDeltaPt_over_PtMatch, dPt_over_pt
                if bestDeltaRMatch <= 0.0001 or bestDeltaPt_over_PtMatch == 0.0001:
                    break
                window_depth -= 1
        if iBest != -1 and bestDeltaRMatch < DELTA_R_CUT:
            # These are the tracks in the reference track collection
            # that have been matched to a track in the comparison
            # track collection
            new_valid[iBest] = False
            original_valid[original_index] = False
            assert original[run] == new[iBest][run], "run mismatch"
            assert original[ls] == new[iBest][ls], "ls mismatch"
            assert original[event_number] == new[iBest][event_number], "event mismatch"
            if debug:
                print original_index
                print original
                print new[iBest]
                print iBest, bestDeltaRMatch, bestDeltaPt_over_PtMatch, '\n'
            histos['num'].Fill(original[pt])
            histos['num_eta'].Fill(original[eta])
            histos['num_phi'].Fill(original[phi])
            histos['num_hits'].Fill(original[hits])
            histos['num_algo'].Fill(original[algo])
            histos['num_orialgo'].Fill(original[orialgo])
            histos['fake_num'].Fill(new[iBest][pt])
            histos['fake_num_eta'].Fill(new[iBest][eta])
            histos['fake_num_phi'].Fill(new[iBest][phi])
            histos['fake_num_hits'].Fill(new[iBest][hits])
            histos['fake_num_algo'].Fill(new[iBest][algo])
            histos['fake_num_orialgo'].Fill(new[iBest][orialgo])
            histos['comparison_algo_vs_reference_algo'].Fill(original[algo], new[iBest][algo])
            histos['comparison_orialgo_vs_reference_orialgo'].Fill(original[orialgo], new[iBest][orialgo])
            histos['comparison_hits_vs_reference_hits'].Fill(original[hits], new[iBest][hits])

    # Let's try a recovery loop with somewhat lesser stringent cuts
    for original_index, original in enumerate(reference):
        if original_valid[original_index]:
            # Now start to look for a matching track in the comparison track collection
            window_depth = 300 # elements to span to look for best candidate
            iBest, bestDeltaRMatch, bestDeltaPt_over_PtMatch = -1, 100, 100
            if debug >=2:
                print "Recovery ", original
            for i,j in enumerate(new):
                if new_valid[i] == True:
                    if debug >=2:
                        print "Recovery  ", i, j
                    if window_depth == 0:
                        break
                    dr, dPt_over_pt = match(original, j)
                    if dr < bestDeltaRMatch and dPt_over_pt < DELTA_PT_OVER_PT_CUT*6:
                        iBest, bestDeltaRMatch, bestDeltaPt_over_PtMatch = i, dr, dPt_over_pt
                    if debug >=2:
                        print "Recovery   ", window_depth, iBest, bestDeltaRMatch, dr, bestDeltaPt_over_PtMatch, dPt_over_pt
                    if bestDeltaRMatch <= 0.0001 or bestDeltaPt_over_PtMatch == 0.0001:
                        break
                    window_depth -= 1
            if iBest != -1 and bestDeltaRMatch < DELTA_R_CUT*10: # inflate cut on DeltaR to recover some good-medium matching
                # These are the tracks in the reference track collection
                # that have been matched to a track in the comparison
                # track collection
                new_valid[iBest] = False
                original_valid[original_index] = False
                if debug:
                    print "Recovery ", original
                    print "Recovery ", new[iBest]
                    print "Recovery ", iBest, bestDeltaRMatch, bestDeltaPt_over_PtMatch
                histos['num'].Fill(original[pt])
                histos['num_eta'].Fill(original[eta])
                histos['num_phi'].Fill(original[phi])
                histos['num_hits'].Fill(original[hits])
                histos['num_algo'].Fill(original[algo])
                histos['num_orialgo'].Fill(original[orialgo])
                histos['fake_num'].Fill(new[iBest][pt])
                histos['fake_num_eta'].Fill(new[iBest][eta])
                histos['fake_num_hits'].Fill(new[iBest][hits])
                histos['fake_num_algo'].Fill(new[iBest][algo])
                histos['fake_num_orialgo'].Fill(new[iBest][orialgo])
                histos['comparison_algo_vs_reference_algo'].Fill(original[algo], new[iBest][algo])
                histos['comparison_orialgo_vs_reference_orialgo'].Fill(original[orialgo], new[iBest][orialgo])
                histos['comparison_hits_vs_reference_hits'].Fill(original[hits], new[iBest][hits])


    # These are the tracks in the reference track collection
    # that have *not* been associated to any track in the
    # comparison collection == > LOST TRACKS
    reference_not_assigned = [j for i,j in enumerate(reference) if original_valid[i]]
    reference_not_assigned.sort(key=lambda tr: tr[algo])
    if debug:
        print "**** Lost tracks **** %d" % len(reference_not_assigned)
    for j in reference_not_assigned:
            histos['lost_hits_vs_algo'].Fill(j[algo], j[hits])
            histos['lost_hits_vs_orialgo'].Fill(j[orialgo], j[hits])
            histos['lost_hits_vs_pt'].Fill(j[pt], j[hits])
            histos['lost_eta'].Fill(j[eta])
            if debug:
                print j
    if debug:
        print "**** End of Lost tracks ****"

    # Fake Tracks
    for i, j in enumerate(new):
        # Fill in the cumulative plots related to tracks in the comparison track collection
        histos['comparison_hits_vs_algo'].Fill(j[algo], j[hits])
        histos['comparison_hits_vs_orialgo'].Fill(j[orialgo], j[hits])
        histos['comparison_hits_vs_pt'].Fill(j[pt], j[hits])
        histos['fake_den'].Fill(j[pt])
        histos['fake_den_eta'].Fill(j[eta])
        histos['fake_den_phi'].Fill(j[phi])
        histos['fake_den_hits'].Fill(j[hits])
        histos['fake_den_algo'].Fill(j[algo])
        histos['fake_den_orialgo'].Fill(j[orialgo])

    # These are the tracks in the comparison track collection
    # that have *not* been associated to any track in the
    # reference collection ==> FAKE TRACKS
    new_not_assigned = [j for i,j in enumerate(new) if new_valid[i]]
    new_not_assigned.sort(key=lambda tr: tr[algo])
    if debug:
        print "**** Fake tracks **** %d" % len(new_not_assigned)
    for j in new_not_assigned:
            histos['fake_hits_vs_algo'].Fill(j[algo], j[hits])
            histos['fake_hits_vs_orialgo'].Fill(j[orialgo], j[hits])
            histos['fake_hits_vs_pt'].Fill(j[pt], j[hits])
            if debug:
                print j
    if debug:
        print "**** End of Fake tracks ****"

def bookHistograms():
    from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F
    histos.setdefault('num', TH1F("numerator_pt", "numerator_pt", 200, 0., 100.))
    histos.setdefault('den', TH1F("denominator_pt", "denominator_pt", 200, 0., 100.))
    histos.setdefault('num_eta', TH1F("numerator_eta", "numerator_eta", 25, -2.5, 2.5))
    histos.setdefault('den_eta', TH1F("denominator_eta", "denominator_eta", 25, -2.5, 2.5))
    histos.setdefault('num_phi', TH1F("numerator_phi", "numerator_phi", 25, -3.15, 3.15))
    histos.setdefault('den_phi', TH1F("denominator_phi", "denominator_phi", 25, -3.15, 3.15))
    histos.setdefault('num_hits', TH1F("numerator_hits", "numerator_hits", 50, 0., 50.))
    histos.setdefault('den_hits', TH1F("denominator_hits", "denominator_hits", 50, 0., 50.))
    histos.setdefault('num_algo', TH1F("numerator_algo", "numerator_algo", 12, -0.5, 11.5))
    histos.setdefault('den_algo', TH1F("denominator_algo", "denominator_algo", 12, -0.5, 11.5))
    histos.setdefault('num_orialgo', TH1F("numerator_orialgo", "numerator_orialgo", 12, -0.5, 11.5))
    histos.setdefault('den_orialgo', TH1F("denominator_orialgo", "denominator_orialgo", 12, -0.5, 11.5))
    histos.setdefault('fake_num', TH1F("fake_numerator_pt", "fake_numerator_pt", 200, 0., 100.))
    histos.setdefault('fake_den', TH1F("fake_denominator_pt", "fake_denominator_pt", 200, 0., 100.))
    histos.setdefault('fake_num_eta', TH1F("fake_numerator_eta", "fake_numerator_eta", 25, -2.5, 2.5))
    histos.setdefault('fake_den_eta', TH1F("fake_denominator_eta", "fake_denominator_eta", 25, -2.5, 2.5))
    histos.setdefault('fake_num_phi', TH1F("fake_numerator_phi", "fake_numerator_phi", 25, -3.15, 3.15))
    histos.setdefault('fake_den_phi', TH1F("fake_denominator_phi", "fake_denominator_phi", 25, -3.15, 3.15))
    histos.setdefault('fake_num_hits', TH1F("fake_numerator_hits", "fake_numerator_hits", 50, 0., 50.))
    histos.setdefault('fake_den_hits', TH1F("fake_denominator_hits", "fake_denominator_hits", 50, 0., 50.))
    histos.setdefault('fake_num_algo', TH1F("fake_numerator_algo", "fake_numerator_algo", 12, -0.5, 11.5))
    histos.setdefault('fake_den_algo', TH1F("fake_denominator_algo", "fake_denominator_algo", 12, -0.5, 11.5))
    histos.setdefault('fake_num_orialgo', TH1F("fake_numerator_orialgo", "fake_numerator_orialgo", 12, -0.5, 11.5))
    histos.setdefault('fake_den_orialgo', TH1F("fake_denominator_orialgo", "fake_denominator_orialgo", 12, -0.5, 11.5))
    histos.setdefault('comparison_algo_vs_reference_algo', TH2F("comparison_algo_vs_reference_algo",
                                                                "comparison_algo_vs_reference_algo",
                                                                12, -0.5, 11.5, 12, -0.5, 11.5))
    histos.setdefault('comparison_orialgo_vs_reference_orialgo', TH2F("comparison_orialgo_vs_reference_orialgo",
                                                                      "comparison_orialgo_vs_reference_orialgo",
                                                                      12, -0.5, 11.5, 12, -0.5, 11.5))
    histos.setdefault('comparison_hits_vs_reference_hits', TH2F("comparison_hits_vs_reference_hits",
                                                                "comparison_hits_vs_reference_hits",
                                                                50, 0., 50., 50, 0., 50.))
    histos.setdefault('reference_hits_vs_algo', TH2F("reference_hits_vs_algo",
                                                     "reference_hits_vs_algo",
                                                     12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('comparison_hits_vs_algo', TH2F("comparison_hits_vs_algo",
                                                      "comparison_hits_vs_algo",
                                                      12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('fake_hits_vs_algo', TH2F("fake_hits_vs_algo",
                                                "fake_hits_vs_algo",
                                                12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('lost_hits_vs_algo', TH2F("lost_hits_vs_algo",
                                                "lost_hits_vs_algo",
                                                12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('reference_hits_vs_orialgo', TH2F("reference_hits_vs_orialgo",
                                                     "reference_hits_vs_orialgo",
                                                     12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('comparison_hits_vs_orialgo', TH2F("comparison_hits_vs_orialgo",
                                                      "comparison_hits_vs_orialgo",
                                                      12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('fake_hits_vs_orialgo', TH2F("fake_hits_vs_orialgo",
                                                "fake_hits_vs_orialgo",
                                                12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('lost_hits_vs_orialgo', TH2F("lost_hits_vs_orialgo",
                                                "lost_hits_vs_orialgo",
                                                12, -0.5, 11.5, 50, 0., 50.))
    histos.setdefault('reference_hits_vs_pt', TH2F("reference_hits_vs_pt",
                                                   "reference_hits_vs_pt",
                                                   200, 0., 100., 50, 0., 50.))
    histos.setdefault('comparison_hits_vs_pt', TH2F("comparison_hits_vs_pt",
                                                    "comparison_hits_vs_pt",
                                                    200, 0., 100., 50, 0., 50.))
    histos.setdefault('fake_hits_vs_pt', TH2F("fake_hits_vs_pt",
                                              "fake_hits_vs_pt",
                                              200, 0., 100., 50, 0., 50.))
    histos.setdefault('lost_hits_vs_pt', TH2F("lost_hits_vs_pt",
                                              "lost_hits_vs_pt",
                                              200, 0., 100., 50, 0., 50.))
    histos.setdefault('lost_eta', TH1F("lost_eta", "lost_eta", 25, -2.5, 2.5))

    for h in histos.keys():
        histos[h].Sumw2()

def fileExists(f):
    import sys
    """Utility to check if the file given in input exists: exit with
    value 1 if it does not exist.
    """

    if not os.path.exists(f):
        print "File %s not found. Quitting.\n" % f
        sys.exit(1)

def initializeGlobals(args):
    from DataFormats.FWLite import Handle, Events
    from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F

    global     eventsRef
    global     eventsNew
    global     tracksRef
    global     tracksNew
    global     label
    global     DELTA_R_CUT
    global     DELTA_PT_OVER_PT_CUT

    fileExists(args.reference)
    fileExists(args.newfile)
    eventsRef = Events(args.reference)
    eventsNew = Events(args.newfile)

    tracksRef = Handle("std::vector<reco::Track>")
    tracksNew = Handle("std::vector<reco::Track>")
    label = args.label
    DELTA_R_CUT = args.deltaR
    DELTA_PT_OVER_PT_CUT = args.deltaPtRel

def runComparison(args):
    from DataFormats.FWLite import Handle, Events
    from ROOT import gROOT, gStyle, TCanvas, TF1, TFile, TTree, gRandom, TH1F, TH2F
    bookHistograms()

    # Since we use Multithreading in processing files, we are not
    # guaranteed that the order of events in the 2 files to compare is
    # the same. For this reason, we loose time with a double loop at
    # the very beginning in order to establish the link between the
    # indices in the 2 input files.
    index_reference = {}
    index_new = {}
    for i in range(0, eventsRef.size()):
      eventsRef.to(i)
      run = eventsRef.eventAuxiliary().run()
      ls = eventsRef.eventAuxiliary().luminosityBlock()
      event_number = eventsRef.eventAuxiliary().event()
      index_reference.setdefault((run, ls, event_number), i)
    for i in range(0, eventsNew.size()):
      eventsNew.to(i)
      run = eventsNew.eventAuxiliary().run()
      ls = eventsNew.eventAuxiliary().luminosityBlock()
      event_number = eventsNew.eventAuxiliary().event()
      index_new.setdefault((run, ls, event_number), i)

    for i in range(0, eventsRef.size()):
    #for i in range(0, 2):
      a = eventsRef.to(i)
      print "Event", i
      a = eventsRef.getByLabel(label, tracksRef)
      run = eventsRef.eventAuxiliary().run()
      ls = eventsRef.eventAuxiliary().luminosityBlock()
      event_number = eventsRef.eventAuxiliary().event()
      trValOri = []
      trValNew = []
      for track in tracksRef.product():
    #   if (track.phi()<0) : continue
    #   if (track.eta()<0) : continue
    #   if (track.pt()<2) : continue
          if args.quality:
              if (track.quality(track.qualityByName(args.quality))) :
                  trValOri.append((10*int(100*track.eta())+track.phi(), "ori", track.eta(), track.phi(), track.pt(),  track.numberOfValidHits() , track.hitPattern().numberOfValidPixelHits(), track.ndof(), track.chi2(), track.algo()-4, track.originalAlgo()-4, track.quality(track.qualityByName("highPurity")), run, ls, event_number))
              else:
                  print 'Ignoring non-highquality track: ', 10*int(100*track.eta())+track.phi(), "ori", track.eta(), track.phi(), track.pt(),  track.numberOfValidHits() , track.hitPattern().numberOfValidPixelHits(), track.ndof(), track.chi2(), track.algo()-4, track.originalAlgo()-4, track.quality(track.qualityByName("highPurity"))
          else:
              trValOri.append((10*int(100*track.eta())+track.phi(), "ori", track.eta(), track.phi(), track.pt(),  track.numberOfValidHits() , track.hitPattern().numberOfValidPixelHits(), track.ndof(), track.chi2(), track.algo()-4, track.originalAlgo()-4, track.quality(track.qualityByName("highPurity")), run, ls, event_number))
      index = None
      if (run, ls, event_number) in index_new.keys():
          index = index_new[(run, ls, event_number)]
      else:
          print "Skipping missing event from comparison file."
          continue
      a = eventsNew.to(index)
      a = eventsNew.getByLabel(label, tracksNew)
      run = eventsNew.eventAuxiliary().run()
      ls = eventsNew.eventAuxiliary().luminosityBlock()
      event_number = eventsNew.eventAuxiliary().event()
      for track in tracksNew.product():
          #   if (track.phi()<0) : continue
          #   if (track.eta()<0) : continue
    #      if (track.pt()<2) : continue
          if args.quality:
              if (track.quality(track.qualityByName(args.quality))) :
                  trValNew.append((10*int(100*track.eta())+track.phi(), "new", track.eta(), track.phi(), track.pt(),  track.numberOfValidHits() , track.hitPattern().numberOfValidPixelHits(), track.ndof(), track.chi2(), track.algo()-4, track.originalAlgo()-4, track.quality(track.qualityByName("highPurity")), run, ls, event_number))
              else:
                  print 'Ignoring non-highquality track: ', 10*int(100*track.eta())+track.phi(), "new", track.eta(), track.phi(), track.pt(),  track.numberOfValidHits() , track.hitPattern().numberOfValidPixelHits(), track.ndof(), track.chi2(), track.algo()-4, track.originalAlgo()-4, track.quality(track.qualityByName("highPurity"))
          else:
              trValNew.append((10*int(100*track.eta())+track.phi(), "new", track.eta(), track.phi(), track.pt(),  track.numberOfValidHits() , track.hitPattern().numberOfValidPixelHits(), track.ndof(), track.chi2(), track.algo()-4, track.originalAlgo()-4, track.quality(track.qualityByName("highPurity")), run, ls, event_number))
      a = trValOri.sort(key=lambda tr: tr[0])
      a = trValNew.sort(key=lambda tr: tr[0])
      compareTwoReco(trValOri, trValNew, histos)

    # Pt
    histos.setdefault('eff', histos['num'].Clone("Efficiency_pt")).SetTitle('Efficiency_pt')
    computeEfficiency(histos['num'], histos['den'], histos['eff'], computeFake=False)
    histos.setdefault('fake', histos['fake_num'].Clone("Fake_pt")).SetTitle('Fake_pt')
    computeEfficiency(histos['fake_num'], histos['fake_den'], histos['fake'], computeFake=True)

    # Eta
    histos.setdefault('eff_eta', histos['num_eta'].Clone("Efficiency_eta")).SetTitle('Efficiency_eta')
    computeEfficiency(histos['num_eta'], histos['den_eta'], histos['eff_eta'], computeFake=False)
    histos.setdefault('fake_eta', histos['fake_num_eta'].Clone("Fake")).SetTitle('Fake_eta')
    computeEfficiency(histos['fake_num_eta'], histos['fake_den_eta'], histos['fake_eta'], computeFake=True)

    # Phi
    histos.setdefault('eff_phi', histos['num_phi'].Clone("Efficiency_phi")).SetTitle('Efficiency_phi')
    computeEfficiency(histos['num_phi'], histos['den_phi'], histos['eff_phi'], computeFake=False)
    histos.setdefault('fake_phi', histos['fake_num_phi'].Clone("Fake")).SetTitle('Fake_phi')
    computeEfficiency(histos['fake_num_phi'], histos['fake_den_phi'], histos['fake_phi'], computeFake=True)

    # Number of valid hits
    histos.setdefault('eff_hits', histos['num_hits'].Clone("Efficiency_hits")).SetTitle('Efficiency_hits')
    computeEfficiency(histos['num_hits'], histos['den_hits'], histos['eff_hits'], computeFake=False)
    histos.setdefault('fake_hits', histos['fake_num_hits'].Clone("Fake")).SetTitle('Fake_hits')
    computeEfficiency(histos['fake_num_hits'], histos['fake_den_hits'], histos['fake_hits'], computeFake=True)

    # Algo
    histos.setdefault('eff_algo', histos['num_algo'].Clone("Efficiency_algo")).SetTitle('Efficiency_algo')
    computeEfficiency(histos['num_algo'], histos['den_algo'], histos['eff_algo'], computeFake=False)
    histos.setdefault('fake_algo', histos['fake_num_algo'].Clone("Fake")).SetTitle('Fake_algo')
    computeEfficiency(histos['fake_num_algo'], histos['fake_den_algo'], histos['fake_algo'], computeFake=True)

    # Orialgo
    histos.setdefault('eff_orialgo', histos['num_orialgo'].Clone("Efficiency_orialgo")).SetTitle('Efficiency_orialgo')
    computeEfficiency(histos['num_orialgo'], histos['den_orialgo'], histos['eff_orialgo'], computeFake=False)
    histos.setdefault('fake_orialgo', histos['fake_num_orialgo'].Clone("Fake")).SetTitle('Fake_orialgo')
    computeEfficiency(histos['fake_num_orialgo'], histos['fake_den_orialgo'], histos['fake_orialgo'], computeFake=True)


def writeHistograms(args):
    from ROOT import TFile
    f = TFile(args.output, "RECREATE")
    producePlots(histos, args.suffix)
    for h in histos.keys():
        histos[h].Write()
    f.Write()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Compare tracks from the same events with 2 difference reconstructions.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-r', '--reference',
                        default='/afs/cern.ch/work/r/rovere/TrackingPOG/RecoRun1vsRecoRun2/CMSSW_7_4_0_pre8/src/relVal_requests/step3RunIReco.root',
                        help='Reference file to be used for the comparison',
                        type=str,
                        required=True)
    parser.add_argument('-n', '--newfile',
                        default='/afs/cern.ch/work/r/rovere/TrackingPOG/RecoRun1vsRecoRun2/CMSSW_7_4_0_pre8/src/relVal_requests/step3.root',
                        help='New file to be used for the comparison',
                        type=str,
                        required=True)
    parser.add_argument('-l', '--label',
                        default='generalTracks',
                        help='Track Collection label to be used for the comparison.',
                        type=str,
                        required=False)
    parser.add_argument('-q', '--quality',
                        help='Quality of the tracks to be used for the comparison.',
                        type=str,
                        required=False)
    parser.add_argument('-d', '--deltaR',
                        default=0.01,
                        help='Delta-R cut to be used for matching tracks between different files.',
                        type=float,
                        required=False)
    parser.add_argument('-p', '--deltaPtRel',
                        default=0.1,
                        help='DeltaPt/Pt cut to be used for matching tracks between different files.',
                        type=float,
                        required=False)
    parser.add_argument('-o', '--output',
                        default='Reco2Reco.root',
                        help='Output ROOT filename.',
                        type=str,
                        required=False)
    parser.add_argument('-s', '--suffix',
                        default='',
                        help='Suffix to be appended to png images.',
                        type=str,
                        required=False)
    parser.add_argument('-b', '--batch',
                        dest='batch_mode',
                        action='store_true',
                        help='Enable batch mode for ROOT.')

    args = parser.parse_args()
    initializeGlobals(args)
    runComparison(args)
    writeHistograms(args)
