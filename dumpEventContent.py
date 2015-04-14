#!/usr/bin/env python

import FWCore.ParameterSet.Config as cms
import argparse
import re

process = cms.Process("Demo")

process.load("Configuration.EventContent.EventContent_cff")


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-l", "--list",
                        action="store_true",
                        help="List all known DataTiers as registered in the central configuration file")
    parser.add_argument("dataTier", help="Supply a dataTier to analyse")
    args = parser.parse_args()

    if args.list:
        print "Known TIERs:"
        for ec in dir(process):
            m = re.match("(.*)EventContent$", ec)
            if m:
                print m.group(1)
    else:
        eventContent = getattr(process, "%sEventContent" % (args.dataTier), None)
        if eventContent:
            try:
                print eventContent.outputCommands
            except:
                print "Something wrong while interpreting dataTier %s" % args.dataTier
                print eventContent
        else:
            print "Unknown DataTier %s\n" % sys.argv[1]
