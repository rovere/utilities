#!/usr/bin/env python

"""Usage: requestDump [-s SERVER] [-n CONNECTIONS] request_label

In order to authenticate to the target server, standard grid certificate
environment must be available. Typically this would be X509_CERT_DIR and
either X509_USER_PROXY or X509_USER_CERT and X509_USER_KEY environment
variables. If these variables are not set, the following defaults are
checked for existence. Note that if the script falls back on using a
key rather than a proxy, it will prompt for the key password.
- $X509_CERT_DIR: /etc/grid-security/certificates
- $X509_USER_KEY: $HOME/.globus/userkey.pem
- $X509_USER_CERT: $HOME/.globus/usercert.pem
"""

from DQMServices.Components.HTTP import RequestManager
from DQMServices.Components.X509 import SSLOptions
import os, sys, re, pycurl, urllib
from optparse import OptionParser
from time import time, strptime, strftime, gmtime
from calendar import timegm
from datetime import datetime
from urlparse import urlparse
from tempfile import mkstemp
from traceback import print_exc
import cjson
import pprint

# HTTP protocol `User-agent` identification string.
ident = "REQDUMP/1.0 python/%s.%s.%s" % sys.version_info[:3]

# SSL/X509 options.
ssl_opts = None

# HTTP request manager for content requests.
reqman = None

# Number of HTTP requests made for content.
nfetched = 0

# Found objects.
found = []

def logme(msg, *args):
  """Generate agent log message."""
  procid = "[%s/%d]" % (__file__.rsplit("/", 1)[-1], os.getpid())
  print datetime.now(), procid, msg % args

def myumask():
  """Get the current process umask."""
  val = os.umask(0)
  os.umask(val)
  return val

def request_init(c, options, server, request, task):
  """`RequestManager` callback to initialise URL of the connection."""

  print server + ((server[-1] != "/" and "/") or "") + urllib.quote(request)
  c.setopt(pycurl.URL, server + ((server[-1] != "/" and "/") or "") + urllib.quote(request))

def parse_request_and_tasks(c):
  options, server, request, task = c.task
  reply = c.buffer.getvalue()
  reply_new = reply.replace("'", '"').replace(" None", ' "NULL"').replace(' True', ' "TRUE"').replace(' False', ' "FALSE"').replace('""', '"')
  m = re.match('.*reqmgr_config_cache/(.*)', server)
  if m:
    o = open("%s_%s.py" % (task, m.group(1)), 'w')
    o.write(reply)
#  print reply
  else:
    reply_new = cjson.decode(reply_new)
    o = open("%s.json" % request, 'w')
    pp = pprint.PrettyPrinter(indent=4, stream=o)
    pp.pprint(reply_new)
    print reply_new
    for i in xrange(10):
      if "Task%d" % i in reply_new.keys():
        print "Analyzing task %d" %i
        reqman.put((options, 'https://cmsweb.cern.ch/couchdb/reqmgr_config_cache/%s' % reply_new["Task%d" % i]['ConfigCacheID'], 'configFile', "Task%d" % i))

# Parse command line options.
op = OptionParser(usage = __doc__)
op.add_option("-s", "--server", dest = "server",
              type = "string", action = "store", metavar = "SERVER",
              default = "https://cmsweb.cern.ch/reqmgr/reqMgr/request/",
              help = "Pull content from SERVER")
op.add_option("-n", "--connections", dest = "connections",
              type = "int", action = "store", metavar = "NUM",
              default = 10, help = "Use NUM concurrent connections")
op.add_option("-v", "--verbose", dest = "verbose",
              action = "store_true", default = False,
              help = "Show verbose scan information")
op.add_option("-r", "--request", dest = "request",
              type = "string", action = "store", metavar = "REQUEST",
              default = "",
              help = "Fetch information on a request and recursively on all its tasks.")
options, args = op.parse_args()
if args:
  print >> sys.stderr, "Too many arguments"
  sys.exit(1)
if not options.server:
  print >> sys.stderr, "Server contact string required"
  sys.exit(1)

UMASK = myumask()

# Get SSL X509 parametres.
ssl_opts = SSLOptions()
if options.verbose:
  print "Using SSL cert dir", ssl_opts.ca_path
  print "Using SSL private key", ssl_opts.key_file
  print "Using SSL public key", ssl_opts.cert_file

# Start a request manager for contents.
reqman = RequestManager(num_connections = options.connections,
                        ssl_opts = ssl_opts,
                        user_agent = ident,
                        request_init = request_init,
                        request_respond = parse_request_and_tasks
                        )

# Process from root directory.
start = time()
reqman.put((options, options.server, options.request, ''))
reqman.process()
end = time()

