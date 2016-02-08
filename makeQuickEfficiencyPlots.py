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
from array import array

subdet = {'PXB': {1:'Layer1', 2:'Layer2', 3:'Layer3'}, 'PXF':{1:'Disk1', 2:'Disk2'}, 'TIB':{1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4'}, 'TID':{1:'wheel1', 2:'wheel2', 3:'wheel3'}, 'TOB':{1:'Layer1', 2:'Layer2', 3:'Layer3', 4:'Layer4', 5:'Layer5', 6:'Layer6'}, 'TEC':{1:'wheel1', 2:'wheel2', 3:'wheel3', 4:'wheel4', 5:'wheel5', 6:'wheel6', 7:'wheel7', 8:'wheel8', 9:'wheel9'}}
#kind = ['', '_barrel', '_endcap']
kind = [''] #, '_barrel', '_endcap']
color = {'_barrel': kAzure+1,
         '_endcap': kGreen+2}

color_for_files = [kOrange, kBlue, kRed, kMagenta, kGreen, kGray]
#f = TFile('quickEfficiencyFromHitPattern_TTbar50ns_CMSSW_7_6_0_pre3.root')
# From SingleMuon
#f = TFile('quickEfficiencyFromHitPattern_Run254833.root')
# From SingleMuon
#f = TFile('quickEfficiencyFromHitPattern_Run254790.root')
#f = TFile('quickEfficiencyFromHitPattern_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_Asympt50ns_MCRUN2_74_V9A-v2.root')
#f = TFile('quickEfficiencyFromHitPattern_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_Asympt25ns_MCRUN2_74_V9A-v3.root')
#f = TFile('quickEfficiencyFromHitPattern_DYJetsToLL_M-50_TuneCUETP8M1_13TeV-amcatnloFXFX-pythia8_Asympt25ns_MCRUN2_74_V9A-v3_pt_5GeV.root')
#f = TFile('quickEfficiencyFromHitPattern_SingleMuPt10_CMSSW_7_6_0_pre3.root')
#f = TFile('quickEfficiencyFromHitPattern_RelValZMM_13_75X_mcRun2_asymptotic_v2-v1_CMSSW_7_6_0_pre3.root')
#f = TFile('quickEfficiencyFromHitPattern_RelValZMM_13_PU50ns_75X_mcRun2_startup_v2-v1_CMSSW_7_6_0_pre3.root')
#f = TFile('quickEfficiencyFromHitPattern_RelValZMM_13_PU25ns_75X_mcRun2_asymptotic_v2-v1_CMSSW_7_6_0_pre3.root')
c = TCanvas("c", "c", 1024, 1024)
   
def printTGraphAsymmErrors(gr, output):
    x_vals = []
    y_vals = []
    y_err_vals = []
    output.write(gr.GetName()+'\n')
#                "0123456789012345678901234567890123456789012345678901234567890"
    output.write(" x value   y value    - y_err / + y_err\n")
    output.write(" -------   -------    -----------------\n")
    for bin in range(0, gr.GetN()):
        output.write("%8.2f  %8.2f    - %5.2f / + %5.2f\n" % (gr.GetX()[bin],
                                                              gr.GetY()[bin]*100.,
                                                              gr.GetErrorYlow(bin)*100,
                                                              gr.GetErrorYhigh(bin)*100))
        x_vals.append(gr.GetX()[bin])
        y_vals.append(gr.GetY()[bin])
        y_err_vals.append(max(gr.GetErrorYlow(bin), gr.GetErrorYhigh(bin)))
    return (x_vals, y_vals, y_err_vals)

def main(args):
    stats = {}
    for d in subdet.keys():
        for sd in subdet[d].keys():
            color_index = -1
            first = True
            l = TLegend(0.1, 0.1, 0.9, 0.3)
            l.SetNColumns(3);
            name = d+subdet[d][sd]
            stats.setdefault(name, [])
            for filename in args.input:
                color_index += 1
                color_index = color_index%len(color_for_files)
                f = TFile(filename)
                output_txt = open("%s%s.txt" % (name, args.suffix), 'w')
                for k in kind:
                    g = f.Get('divide_Hits_ok_%s%s_by_Hits_ok_and_missing_%s%s' % (name, k, name, k))
                    stats[name].append(printTGraphAsymmErrors(g, output_txt))
                    g.SetMinimum(0.6)
                    g.SetMaximum(1.0)
                    g.SetMarkerStyle(kFullCircle)
                    if len(args.input) > 1:
                        g.SetLineColor(color_for_files[color_index])
                        g.SetMarkerColor(color_for_files[color_index])
                    elif  k in color.keys():
                        g.SetLineColor(color[k])
                        g.SetMarkerColor(color[k])
                    else:
                        g.SetLineColor(kOrange+10)
                        g.SetMarkerColor(kOrange+10)
                    l.AddEntry(g, filename.replace('.root',''), 'len')
                    if first:
                        first = False
                        g.Draw('AP')
                        if args.bxaxis:
                            g.GetXaxis().SetLimits(0., 4000.)
                        else:
                            g.GetXaxis().SetLimits(0., 40.)
                        g.Draw('AP')
                    else:
                        g.Draw('P SAME')
            if args.legend:
                l.Draw()
            c.SaveAs('%s%s.png' % (name, args.suffix))
            print stats[name]
    for d in subdet.keys():
        for sd in subdet[d].keys():
            name = d+subdet[d][sd]
            output_root_file = TFile("%s%s.root" % (name, args.suffix), "RECREATE")
            x = array('f')
            y = array('f')
            y_err = array('f')
            x_err = array('f')
            for (x_values, y_values, y_err_values) in stats[name]:
                for i in range(len(x_values)):
                    x.append(x_values[i])
                    y.append(y_values[i])
                    x_err.append(0.)
                    y_err.append(y_err_values[i])
            print name, x, y
            gr = TGraphErrors(len(x), x, y, x_err, y_err)
            gr.Write()
            output_root_file.Close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Quick Efficiency from HitPattern.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-i', '--input',
                        nargs='+',
                        help='Input files to be used to produce the plots. If more than one file supplied, make overlay of same det-subdet on the same plot for different files.',
                        type=str,
                        required=False)
    parser.add_argument('-s', '--suffix',
                        help='Suffix to be used while producing png and txt files.',
                        type=str,
                        default='',
                        required=True)
    parser.add_argument('-x', '--bxaxis',
                        help='Turn the X-Axis into BX and not number of vertices.',
                        default=False,
                        action = 'store_true')
    parser.add_argument('-l', '--legend',
                        help='Add a legend to the final plot using the input filename as text.',
                        default=False,
                        action = 'store_true')
    args = parser.parse_args()
    main(args)
