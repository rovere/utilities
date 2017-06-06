#!/usr/bin/env python

# Before running:
# source /cvmfs/cms.cern.ch/crab3/crab.sh

import pprint
from dbs.apis.dbsClient import DbsApi

url="https://cmsweb.cern.ch/dbs/prod/global/DBSReader"
api=DbsApi(url=url)
f = api.listFiles(run_num='296075', dataset='/ExpressPhysics/Run2017A-Express-v1/FEVT')
lumis = [api.listFileLumiArray(logical_file_name=ff['logical_file_name']) for ff in f]
lumis.sort(key=lambda x : x[0]['lumi_section_num'])
lumi_file = ["%s %s" % (x[0]['lumi_section_num'],x[0]['logical_file_name']) for x in lumis ]
pprint.pprint(lumi_file)
