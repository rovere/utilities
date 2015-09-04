#!/usr/bin/env python

# Pure trick to start ROOT in batch mode, pass this only option to it
# and the rest of the command line options to this code.
import sys
oldargv = sys.argv[:]
sys.argv = [ '-b-' ]
from ROOT import *
gROOT.SetBatch(True)
sys.argv = oldargv

import argparse

subdet = {'PXB': {1:'Layer1', 2:'Layer2', 3:'Layer3'}, 'PXF':{1:'Disk1', 2:'Disk2'}, 'TIB':{1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4'}, 'TID':{1:'wheel1', 2:'wheel2', 3:'wheel3'}, 'TOB':{1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4', 5:'Layer5', 6:'Layer6'}, 'TEC':{1:'wheel1', 2:'wheel2', 3:'wheel3', 4:'wheel4', 5:'wheel5', 6:'wheel6', 7:'wheel7', 8:'wheel8', 9:'wheel9'}}
kind = ['', '_barrel', '_endcap']
color = {'_barrel': kAzure+1,
         '_endcap': kGreen+2}

#f = TFile('quickEfficiencyFromHitPattern_TTbar50ns_CMSSW_7_6_0_pre3.root')
# From SingleMuon
#f = TFile('quickEfficiencyFromHitPattern_Run254833.root')
# From SingleMuon
#f = TFile('quickEfficiencyFromHitPattern_Run254790.root')
f = TFile('quickEfficiencyFromHitPattern_Run251562_ZeroBias.root')
#f = TFile('quickEfficiencyFromHitPattern_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_Asympt50ns_MCRUN2_74_V9A-v2.root')
#f = TFile('quickEfficiencyFromHitPattern_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_Asympt25ns_MCRUN2_74_V9A-v3.root')
#f = TFile('quickEfficiencyFromHitPattern_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_Asympt25ns_MCRUN2_74_V9A-v3_pt_5GeV.root')
#f = TFile('quickEfficiencyFromHitPattern_SingleMuPt10_CMSSW_7_6_0_pre3.root')
#f = TFile('quickEfficiencyFromHitPattern_RelValZMM_13_75X_mcRun2_asymptotic_v2-v1_CMSSW_7_6_0_pre3.root')
#f = TFile('quickEfficiencyFromHitPattern_RelValZMM_13_PU50ns_75X_mcRun2_startup_v2-v1_CMSSW_7_6_0_pre3.root')
#f = TFile('quickEfficiencyFromHitPattern_RelValZMM_13_PU25ns_75X_mcRun2_asymptotic_v2-v1_CMSSW_7_6_0_pre3.root')
c = TCanvas("c", "c", 1024, 1024)
   
def printTGraphAsymmErrors(gr, output):
    output.write(gr.GetName()+'\n')
#                "0123456789012345678901234567890123456789012345678901234567890"
    output.write(" x value   y value    - y_err / + y_err\n")
    output.write(" -------   -------    -----------------\n")
    for bin in range(0, gr.GetN()):
        output.write("%8.2f  %8.2f    - %5.2f / + %5.2f\n" % (gr.GetX()[bin],
                                                              gr.GetY()[bin]*100.,
                                                              gr.GetErrorYlow(bin)*100,
                                                              gr.GetErrorYhigh(bin)*100))
                     
for d in subdet.keys():
    for sd in subdet[d].keys():
        name = d+subdet[d][sd]
        first = True
        l = TLegend(0.6, 0.1, 0.9, 0.2)
        output_txt = open("%s.txt" % name, 'w')
        for k in kind:
            g = f.Get('divide_Hits_ok_%s%s_by_Hits_ok_and_missing_%s%s' % (name, k, name, k))
            printTGraphAsymmErrors(g, output_txt)
            g.SetMinimum(0.7)
            g.SetMaximum(1.0)
            g.SetMarkerStyle(kFullCircle)
            if k in color.keys():
                g.SetLineColor(color[k])
                g.SetMarkerColor(color[k])
            else:
                g.SetLineColor(kOrange+10)
                g.SetMarkerColor(kOrange+10)
            l.AddEntry(g)
            if first:
                first = False
                g.Draw('AP')
                g.GetXaxis().SetLimits(0., 40.)
                g.Draw('AP')
            else:
                g.Draw('P SAME')
        l.Draw()
        c.SaveAs('%s.png' % name)
