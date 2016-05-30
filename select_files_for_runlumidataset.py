#!/usr/bin/env python

import argparse
from dbs.apis.dbsClient import DbsApi

_PREFIX = 'root://eoscms.cern.ch//eos/cms/'

def getFilesForQuery(args):
  global _PREFIX

  query = {
    'dataset' : args.dataset,
    'run_num': args.run,
    'lumi_list': [l for l in range(args.ls_min, args.ls_max+1)]
    }

  api = DbsApi(url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader")
  files = api.listFiles(**query)

  o = open("file_list_%d_LS%d-%d.txt" % (args.run, args.ls_min, args.ls_max), 'w')
  o.write(' '.join([_PREFIX + f['logical_file_name'] for f in files]))
  o.close()

def main():
  parser = argparse.ArgumentParser(description='Locally donwload the list of files for a specific (dataset,run,[ls]) combination')
  parser.add_argument('-l', '--ls_min',
                      help='Minimum Lumisection to consider, inclusive',
                      default=1,
                      type=int,
                      required=True)
  parser.add_argument('-m', '--ls_max',
                      help='Maximum Lumisection to consider, inclusive',
                      default=10,
                      type=int,
                      required=True)
  parser.add_argument('-d', '--dataset',
                      help='Dataset from which to extract the list of files',
                      default='/ExpressPhysics/Run2016B-Express-v2/FEVT',
                      type=str,
                      required=True)
  parser.add_argument('-r', '--run',
                      help='Run Number to consider',
                      type=int,
                      default=273158,
                      required=True)
  args = parser.parse_args()

  getFilesForQuery(args)

if __name__ == '__main__':
  main()
