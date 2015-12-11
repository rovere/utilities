#!/usr/bin/env python
import argparse
import sys
from array import array
from struct import unpack
from math import sqrt

def doWork(args):
    from DataFormats.FWLite import Handle, Events
    from ROOT import TGraphErrors, TFile, gROOT, kOrange
    output_file = None
    gr = None
    if not args.files:
        return
    tracks_h = Handle("std::vector<reco::Track>")
    counter = 0
    x_squared_mean = [0. for i in range(len(args.files))]
    x_mean = [0. for i in range(len(args.files))]
    normalization = [0. for i in range(len(args.files))]
    rms =  [0. for i in range(len(args.files))]
    barrel_hits_squared_mean = [0. for i in range(len(args.files))]
    barrel_hits_mean = [0. for i in range(len(args.files))]
    barrel_hits_normalization = [0. for i in range(len(args.files))]
    barrel_hits_rms =  [0. for i in range(len(args.files))]
    for input_file in args.files:
        events = Events(input_file)
        for e in range(events.size()):
            no_reason_to_stop = 0.
            ccc_stop_reason = 0.
            a = events.to(e)
            a = events.getByLabel("generalTracks", tracks_h)
            for track in range(tracks_h.product().size()):
                t = tracks_h.product()[track]
                # take care of barrel hits calculation. Later
                # calculation goes further down since they also "skim"
                # events. For the barrel hits calculation, we only
                # consider tracks with abs(eta) < 0.8 and of
                # highPurity quality.
                if t.quality(t.qualityByName('highPurity')) and abs(t.eta()) < 0.8 and t.pt() > 0.65:
                    barrel_hits_mean[counter] += t.numberOfValidHits()
                    barrel_hits_squared_mean[counter] += t.numberOfValidHits()**2
                    barrel_hits_normalization[counter] += 1.
                if args.quality and args.quality != 'ANY':
                    if not t.quality(t.qualityByName(args.quality)):
                        continue
                stop_reason = int(unpack('@B', t.stopReason())[0])
                if stop_reason == 255:
                    no_reason_to_stop += 1
                if stop_reason == 8:
                    ccc_stop_reason += 1
            if no_reason_to_stop == 0 or ccc_stop_reason == 0:
                continue
            x_mean[counter] += ccc_stop_reason/no_reason_to_stop
            x_squared_mean[counter] += (ccc_stop_reason/no_reason_to_stop)**2
            normalization[counter] += 1
        x_mean[counter] = x_mean[counter]/normalization[counter]
        x_squared_mean[counter] = x_squared_mean[counter]/normalization[counter]
        rms[counter] = sqrt(x_squared_mean[counter] - x_mean[counter]**2)
        print '%s: mean and RMS: %f, %f, normalized to lumi mean and RMS: %f, %f' % (input_file,
                                                                                     x_mean[counter],
                                                                                     rms[counter],
                                                                                     x_mean[counter]/args.instlumis[counter],
                                                                                     rms[counter]/args.instlumis[counter])
        barrel_hits_mean[counter] = barrel_hits_mean[counter]/barrel_hits_normalization[counter]
        barrel_hits_squared_mean[counter] = barrel_hits_squared_mean[counter]/barrel_hits_normalization[counter]
        barrel_hits_rms[counter] = sqrt(barrel_hits_squared_mean[counter] - barrel_hits_mean[counter]**2)
        print '%s: Barrel Hits mean and RMS: %f, %f, normalized to lumi mean and RMS: %f, %f' % (input_file,
                                                                                                 barrel_hits_mean[counter],
                                                                                                 barrel_hits_rms[counter],
                                                                                                 barrel_hits_mean[counter]/args.instlumis[counter],
                                                                                                 barrel_hits_rms[counter]/args.instlumis[counter])
        counter += 1
    if args.output:
        output_file = TFile(args.output, "RECREATE")
        output_file.cd()
        x_mean_arr = array('f')
        x_mean_arr.fromlist(x_mean)
        rms_arr = array('f')
        rms_arr.fromlist(rms)
        lumis = array('f')
        lumis.fromlist(args.instlumis)
        lumi_errors = array('f')
        lumi_errors.fromlist([0. for i in range(len(args.instlumis))])
        gr = TGraphErrors(len(lumis), lumis, x_mean_arr, lumi_errors, rms_arr)
        gr.SetTitle("Average CCCTF lost hits/full Trajectories vs Inst. Luminosity")
        gr.SetMarkerStyle(22)
        gr.SetMarkerColor(kOrange)
        gr.SetLineColor(kOrange)
        gr.Write()
        barrel_hits_mean_arr = array('f')
        barrel_hits_mean_arr.fromlist(barrel_hits_mean)
        barrel_hits_rms_arr = array('f')
        barrel_hits_rms_arr.fromlist(barrel_hits_rms)
        gr2 = TGraphErrors(len(lumis), lumis, barrel_hits_mean_arr, lumi_errors, barrel_hits_rms_arr)
        gr2.SetTitle("Average Barrel Hits vs Inst. Luminosity")
        gr2.SetMarkerStyle(22)
        gr2.SetMarkerColor(kOrange)
        gr2.SetLineColor(kOrange)
        gr2.Write()
        output_file.Close()

def checkArgs(args):
    if args.files and not args.instlumis:
        print "Maybe you forgot to supply also the luminosity information for the supplied files ...? Quitting."
        sys.exit(1)
    if args.instlumis and not args.files:
        print "Maybe you forgot to supply also the files for the supplied luminosities ...? Quitting."
        sys.exit(1)
    if args.files and args.instlumis and not (len(args.files) == len(args.instlumis)):
        print "The number of files and instantaneous luminosities supplied does not match. Quitting."
        sys.exit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Derive the behaviour of HIP-related quantities for many files, better if at different inst.lumi.',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('-f', '--files',
                        action = 'store',
                        type = str,
                        nargs = '+',
                        help = 'Files to be processed')
    parser.add_argument('-i', '--instlumis',
                        action = 'store',
                        type = float,
                        nargs = '+',
                        help = "Instantaneous luminosities associated to the supplied files. The ordering **MUST** follow the ones of --files.")
    parser.add_argument('-q', '--quality',
                        default = 'ANY',
                        nargs = '?',
                        choices= ['ANY', 'highPurity', 'loose', 'tight'],
                        help = 'Select tracks with the specified quality only. ANY means select all tracks in the collection.',
                        type = str)
    parser.add_argument('-o', '--output',
                        help = 'Output ROOT files that will store the results',
                        type = str)
    args = parser.parse_args()
    checkArgs(args)
    doWork(args)
