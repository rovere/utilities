#!/usr/bin/env python

import os, sys
# Pure trick to start ROOT in batch mode, pass this only option to it
# and the rest of the command line options to this code.
oldargv = sys.argv[:]
sys.argv = [ '-b-' ]
import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import TFile, TChain, TCanvas, TH1F, gStyle, kRed, gSystem, gROOT
sys.argv = oldargv
import argparse
import array
import re

dataChain = None
mcChain = None
MAX_ENTRIES = 1000000000000
PUweights = []
c = TCanvas("GenericCanvas", "GenericCanvas", 1024, 1024)
gStyle.SetOptStat(0)

def cut_string_for_mc(cut_string):
    return re.sub('(.*)', 'weight(nvertex)*(\\1)', cut_string)

def createWeightHisto(args):
    global PUweights
    dataChain.Draw("nvertex>>vertices_data(100, 0, 100)", "", "",   MAX_ENTRIES, 0)
    mcChain.Draw("nvertex>>vertices_mc(100, 0, 100)", "", "",   MAX_ENTRIES, 0)
    vertices_mc = gROOT.Get("vertices_mc")
    vertices_data = gROOT.Get("vertices_data")
    print [vertices_data.GetBinContent(i) for i in xrange(vertices_data.GetNbinsX())]
    print [vertices_mc.GetBinContent(i) for i in xrange(vertices_mc.GetNbinsX())]
#    vertices_data.Scale(1./vertices_data.GetEntries())
#    vertices_mc.Scale(1./vertices_mc.GetEntries())
    vertices_mc.Scale(1./vertices_mc.GetEntries())
    vertices_data.Divide(vertices_mc)
    norm = vertices_data.GetEntries()
    PUweights = [vertices_data.GetBinContent(i)/float(norm) for i in xrange(vertices_data.GetNbinsX())]
    print PUweights
    
def createWeightFunction(args):
    global PUweights
    createWeightHisto(args)
    weight_initializer = "{ %f" % PUweights[0]
    for pu in range(1, len(PUweights) - 1):
        weight_initializer += ", %8.7f" % PUweights[pu]
    weight_initializer += ", %f };" % PUweights[-1]
    output_file = open("weight.C", "w")
    output_file.write("float weight(int var) {\n")
    output_file.write(" float weights[%d] = %s\n" % (len(PUweights), weight_initializer))
    output_file.write(" return weights[var];}\n")
    output_file.close()
    gSystem.CompileMacro("weight.C")

def compareHits(args):
    global dataChain, mcChain, c
    cut_string = args.cut_tracks
    cut_string_mc = cut_string_for_mc(cut_string)
    for det in ['', 'TIB', 'TOB', 'TID', 'TEC']:
        dataChain.Draw("track_numberOfValidStrip%sHits:track_eta" % det, cut_string, "prof",   MAX_ENTRIES, 0)
        mcChain.Draw("track_numberOfValidStrip%sHits:track_eta" % det, cut_string_mc, "prof same", MAX_ENTRIES, 0)
        c.SaveAs("HitsStrip%s_vs_Eta.png" % det)
    for det in ['', 'Barrel', 'Endcap']:
        dataChain.Draw("track_numberOfValidPixel%sHits:track_eta" % det, cut_string, "prof",   MAX_ENTRIES, 0)
        mcChain.Draw("track_numberOfValidPixel%sHits:track_eta" % det, cut_string_mc, "prof same", MAX_ENTRIES, 0)
        c.SaveAs("HitsPixel%s_vs_Eta.png" % det)
    dataChain.Draw("(track_numberOfValidStripHits+track_numberOfValidPixelHits):track_eta", cut_string, "prof",   MAX_ENTRIES, 0)
    mcChain.Draw("(track_numberOfValidStripHits+track_numberOfValidPixelHits):track_eta", cut_string_mc, "prof same",   MAX_ENTRIES, 0)
    c.SaveAs("HitsPixelAndStrip_vs_Eta.png")

def compareTrackParamters(args):
    global dataChain, mcChain
    cut_string = args.cut_tracks
    cut_string_mc = cut_string_for_mc(cut_string)
    dataChain.Draw("ntrack", "ntrack !=0","norm",   MAX_ENTRIES, 0)
    if args.weight:
        mcChain.Draw("ntrack", cut_string_for_mc("ntrack !=0"), "norm same", MAX_ENTRIES, 0)
    else:
        mcChain.Draw("ntrack", cut_string_for_mc("ntrack !=0"), "norm same", MAX_ENTRIES, 0)
    c.SaveAs("NumTracks.png")
    for param in ['pt', 'eta', 'phi', 'dxy', 'dz',
                  'chi2',
                  'algo'
                  ]:
        dataChain.Draw("track_%s" % param, cut_string, "norm",   MAX_ENTRIES, 0)
        mcChain.Draw("track_%s" % param, cut_string_mc, "norm same", MAX_ENTRIES, 0)
        c.SaveAs("Track_%s.png" % param)
    c.SetLogy(1)
    for param in [
        'numberOfValidHits',
        'numberOfTrackerHits',
        'numberOfValidTrackerHits',
        'numberOfValidPixelHits',
        'numberOfValidPixelBarrelHits',
        'numberOfValidPixelEndcapHits',
        'numberOfValidStripHits',
        'numberOfValidStripTIBHits',
        'numberOfValidStripTIDHits',
        'numberOfValidStripTOBHits',
        'numberOfValidStripTECHits',
        'numberOfLostInnerHits',
        'numberOfLostInnerPixelHits',
        'numberOfLostInnerPixelBarrelHits',
        'numberOfLostInnerPixelEndcapHits',
        'numberOfLostInnerStripHits',
        'numberOfLostInnerStripTIBHits',
        'numberOfLostInnerStripTIDHits',
        'numberOfLostInnerStripTOBHits',
        'numberOfLostInnerStripTECHits',
        'numberOfLostOuterHits',
        'numberOfLostOuterPixelHits',
        'numberOfLostOuterPixelBarrelHits',
        'numberOfLostOuterPixelEndcapHits',
        'numberOfLostOuterStripHits',
        'numberOfLostOuterStripTIBHits',
        'numberOfLostOuterStripTIDHits',
        'numberOfLostOuterStripTOBHits',
        'numberOfLostOuterStripTECHits'
        ]:
        dataChain.Draw("track_%s" % param, cut_string, "norm",   MAX_ENTRIES, 0)
        mcChain.Draw("track_%s" % param, cut_string_mc, "norm same", MAX_ENTRIES, 0)
        c.SaveAs("Track_%s.png" % param)
    c.SetLogy(0)


def compareVertexParamters(args):
    global dataChain, mcChain
    cut_string = args.cut_vertices
    cut_string_mc = cut_string_for_mc(cut_string)
    print cut_string_mc
    dataChain.Draw("nvertex", cut_string, "norm",   MAX_ENTRIES, 0)
    mcChain.Draw("nvertex", cut_string_mc, "norm same", MAX_ENTRIES, 0)
    c.SaveAs("NumVertices.png")
    for param in ['ndof',
                  'normalizedChi2',
                  'nTracks'
                  ]:
        dataChain.Draw("vertex_%s" % param, cut_string, "norm",   MAX_ENTRIES, 0)
        mcChain.Draw("vertex_%s" % param, cut_string_mc, "norm same", MAX_ENTRIES, 0)
        c.SaveAs("Vertex_%s.png" % param)
    
def createTChains(args):
    global dataChain, mcChain
    dataChain = TChain('Tracks')
    mcChain = TChain('Tracks')
    mcChain.SetLineColor(kRed)
    for f in args.data:
        dataChain.Add(f)
    for f in args.mc:
        mcChain.Add(f)
    print 'Data Events: %d' % dataChain.GetEntries()
    print 'MC   Events: %d' % mcChain.GetEntries()

if __name__ == '__main__':
  parser = argparse.ArgumentParser(description='Quick Data/MC comparison Tool for tracks.',
                                   formatter_class=argparse.ArgumentDefaultsHelpFormatter)
  parser.add_argument('-d', '--data',
                      help='One or more input DATA files.',
                      type=str,
                      nargs='+',
                      required=True)
  parser.add_argument('-m', '--mc',
                      help='One or more input MC files.',
                      type=str,
                      nargs='+',
                      required=True)
  parser.add_argument('-t', '--cut_tracks',
                      help='Additional cut-string that will be applied in all plots',
                      type=str,
                      required=False,
                      default='')
  parser.add_argument('-v', '--cut_vertices',
                      help='Additional cut-string that will be applied in all plots',
                      type=str,
                      required=False,
                      default='')
  parser.add_argument('-w', '--weight',
                      help='Use PU reweight(applied on MC to resemble DATA)',
                      required=False,
                      action='store_true')
  args = parser.parse_args()

  createTChains(args)
  print args
  if args.weight:
      createWeightFunction(args)
#  compareHits(args)
#  compareTrackParamters(args)
  compareVertexParamters(args)
