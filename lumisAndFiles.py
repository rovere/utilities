#!/usr/bin/env python

# Before running:
# source /cvmfs/cms.cern.ch/crab3/crab.sh

import pprint
from dbs.apis.dbsClient import DbsApi

url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
api=DbsApi(url=url)
#f = api.listFiles(dataset='/ExpressPhysics/Run2017B-Express-v1/FEVT',run_num=297562)
f = api.listFiles(dataset='/JetHT/Run2017B-v1/RAW',run_num=297484)
lumis = [api.listFileLumiArray(logical_file_name=ff['logical_file_name']) for ff in f]
lumis.sort(key=lambda x : x[0]['lumi_section_num'])
#lumi_file = ["%s %s" % (x[0]['lumi_section_num'],x[0]['logical_file_name']) for x in lumis ]
lumi_file = {}
for x in lumis:
  for j in x[0]['lumi_section_num']:
    lumi_file[j] = x[0]['logical_file_name']
pprint.pprint(lumi_file)
