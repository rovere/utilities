#!/usr/bin/env python

import FWCore.ParameterSet.Config as cms
import argparse
import re
import copy
import sys

process = cms.Process("Demo")

process.load("Configuration.EventContent.EventContent_cff")
process.load("Configuration.EventContent.AlCaRecoOutput_cff")

# Special ALCA Stuff
def processAlcaStuff():
    res = {}
    process.load("Configuration.StandardSequences.AlCaRecoStreams_cff")
    alcaConfig = sys.modules["Configuration.StandardSequences.AlCaRecoStreams_cff"]
    for alcaName in alcaConfig.__dict__.keys():
        alcastream = getattr(alcaConfig, alcaName)
        shortName = alcaName.replace('ALCARECOStream','')
        output = copy.deepcopy(process.ALCARECOEventContent.outputCommands)
        if isinstance(alcastream, cms.FilteredStream):
            output.extend(getattr(process, 'OutALCARECO' + shortName + '_noDrop').outputCommands)
            res[alcaName] = copy.deepcopy(output)
    return res

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list",
                        action="store_true",
                        help="List all known DataTiers as registered in the central configuration file",
                        required=False)
    parser.add_argument("-d", "--dataTier",
                        help="Supply a dataTier to analyse")
    parser.add_argument("-a", "--alcaStream",
                        help="Supply an AlCaStream to analyse")
    args = parser.parse_args()

    if args.list:
        print "Known TIERs:"
        for ec in dir(process):
            m = re.match("(.*)EventContent$", ec)
            if m:
                print m.group(1)
        alca = processAlcaStuff()
        print "Known AlcaStreams:"
        for i in alca.keys():
            print i
    if args.dataTier:
        eventContent = getattr(process, "%sEventContent" % (args.dataTier), None)
        if eventContent:
            try:
                print eventContent.outputCommands
            except:
                print "Something wrong while interpreting dataTier %s" % args.dataTier
                print eventContent
        else:
            print "Unknown DataTier %s\n" % args.dataTier
    if args.alcaStream:
        alca = processAlcaStuff()
        if args.alcaStream in alca.keys():
            print "%s\n" % args.alcaStream, alca[args.alcaStream]
        else:
            print "Unknown AlCaStream %s\n" % args.alcaStream
