#!/bin/env python

import httplib
import urllib
import os
import pprint
import json
pp = pprint.PrettyPrinter(indent=4)


req_name='cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011A_Jet_Run2011A-v1_RAW_111115_160930'
url= 'cmsweb.cern.ch'
url_old='localhost:8687'
headers  =  {"Content-type": "application/x-www-form-urlencoded","Accept": "text/plain"}

def get_req_info(req_name):
  print "Processing Request: \033[1m%s\033[0m ..." %req_name
  conn  =  httplib.HTTPSConnection(url, cert_file = os.getenv('X509_USER_PROXY'), key_file = os.getenv('X509_USER_PROXY'))
  conn.request("GET",  "/reqmgr/reqMgr/request/%s"%req_name,'',headers)
  response = conn.getresponse()
  data = eval(response.read())
  return data

def get_req_info_old(req_name):
  conn  =  httplib.HTTPConnection(url_old)
  conn.request("GET",  "/reqmgr/reqMgr/request/%s"%req_name,'',headers)
  response = conn.getresponse()  
  data = eval(response.read())  
  return data

def get_outputdataset(req_name):
  conn  =  httplib.HTTPConnection(url_old)
  conn.request("GET",  "/reqmgr/reqMgr/outputDatasetsByRequestName/%s"%req_name,'',headers)
  response = conn.getresponse()  
  data = eval(response.read())  
  return data

def list2date(datelist):
  # format is [2011, 11, 19, 0, 4, 18],
  year,month,day,boh1,boh2,boh3=datelist
  return "%s-%s-%s" %(day,month,year)

def print_req_info(req_name,req_info,verbose=False):  

  if not verbose and not req_info.has_key('exception'):
    if req_info.has_key('RequestName'):
      print "Request Name: %s" %req_info['RequestName']
    if req_info.has_key('RequestDate'):
      print " o Submission date: %s" %list2date(req_info['RequestDate'])
    status=req_info['RequestStatus']    
    print " o Request Status: \033[1m%s\033[0m" %status
    print " o Percent Complete (success): \033[1m%s (%s)\033[0m" %(req_info['percent_complete'],req_info['percent_success'])
    if status == "announced":
      print " o Datasets:"
      counter=1
      for dataset in get_outputdataset(req_name):
        print "   %s) \033[1m%s\033[0m"%(counter,dataset)
        counter+=1
  else:
    pp.pprint(req_info)
  print "*"*80

requests=['cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011A_Jet_Run2011A-v1_RAW_111115_160924',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011A_Jet_Run2011A-v1_RAW_111115_160926',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011A_Jet_Run2011A-v1_RAW_111115_160929',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011A_Jet_Run2011A-v1_RAW_111115_160930',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011B_Jet_Run2011B-v1_RAW_111115_160938',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011B_Jet_Run2011B-v1_RAW_111115_160940',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011B_Jet_Run2011B-v1_RAW_111115_160942',
'cmsdataops_CMSSW_4_2_8_patch6_HiggsReproForCert2011B_Jet_Run2011B-v1_RAW_111115_160944']

for request in requests:  
  req_info = get_req_info(request)
  if req_info.has_key('exception'):
    print "---> It did not work, old reqmngr (the one with the tunnel)"
    req_info = get_req_info_old(request)
  print_req_info(request,req_info)

