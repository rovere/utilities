#!/usr/bin/env python

import cjson
import StringIO
import pycurl
import re
from githubAPI import github_api_token

def head():
  head = """<!DOCTYPE html>
<html>
<head>
<title>Release Notes Summary Page</title>
</head>
<script type="text/javascript"
src="https://c328740.ssl.cf1.rackcdn.com/mathjax/latest/MathJax.js?config=TeX-AMS-MML_HTMLorMML">
</script>


<body>
<xmp theme="cerulean" style="display:none;">

"""
  return head

def trail():
  trail = """
<p>
    <div style="text-align: center; width: 146px; margin: 0 auto">
        <button type="button" class="btn btn-info" onclick="var cur = window.location.href; window.location.href = cur.replace(/(.*)/.*.html$/, '$1/');">Main Minutes Page</button>
    </div>
</p>

</xmp>

<!-- <script src="http://strapdownjs.com/v/0.2/strapdown.js"></script> -->

<!-- For internal CERN documents we cannot do x-loads..?? Moreover I
patched strapdown to be able to manage bootswatch v3.0, so we need to
use our own local installation. -->

<script src="../strapdown/v/0.2/strapdown.js"></script>
</body>
"""
  return trail

def getReleasesNotes():
  RX_LINKS = re.compile('^Link: <(.*?)>; rel="next", <(.*?)>; rel="last"')
  RX_RELEASE = re.compile('CMSSW_(\d+)_(\d+)_(\d+)(_pre[0-9]+)*(_cand[0-9]+)*')
  RX_COMMIT = re.compile(".*\#(\d{0,5})( from.*)")
  RX_COMPARE = re.compile("(^https://github.*compare.*\.\.\..*)")
  next_link = 'first'
  last_link = 'last'
  current_link = "https://api.github.com/repos/cms-sw/cmssw/releases"
  response = StringIO.StringIO()
  header   = StringIO.StringIO()
  c = pycurl.Curl()
  c.setopt(pycurl.URL, current_link)
  c.setopt(pycurl.WRITEFUNCTION, response.write)
  c.setopt(pycurl.HEADERFUNCTION, header.write)
  c.setopt(pycurl.HTTPHEADER, ['Authorization: token %s' % github_api_token])
  counter = -1
  notes = []

  while next_link != last_link:
    c.perform()

    releases = cjson.decode(response.getvalue())
    headers = header.getvalue()
#    print releases, headers
    for line in headers.split('\n'):
       m = re.match(RX_LINKS, line)
       if m:
          next_link = m.group(1)
          last_link = m.group(2) 
          c.setopt(pycurl.URL, next_link)
          print '%s, [%s,%s]' % (line, next_link, last_link)

    for i in range(len(releases)):
      counter += 1
      rel_numbers = re.match(RX_RELEASE, releases[i]['name'])
      if rel_numbers:
#        print rel_numbers.groups()
#        print releases[i]
        release_notes = re.sub(RX_COMMIT, '\\n1. [\\1](http://github.com/cms-sw/cmssw/pull/\\1) \\2', releases[i]['body'])
        release_notes = re.sub(RX_COMPARE, '\\1\n\n', release_notes)
#        print release_notes
        notes.append([int(rel_numbers.group(1)),
                      int(rel_numbers.group(2)),
                      int(rel_numbers.group(3)),
                      rel_numbers.group(4),
                      rel_numbers.group(5),
                      releases[i]['name'],
                      release_notes
                     ])
#        print "%d. %s" % (counter, releases[i]['name'])
    response.seek(0)
    response.truncate()
    header.seek(0)
    header.truncate()

  current = 0
  out_rel = None
  notes = sorted(notes, key = lambda x: (x[0], x[1], x[2], x[3], x[4]), reverse=True)
  for r in notes:
    new_current = int(r[0])*100 + int(r[1])
    if new_current != current:
      if out_rel:
        out_rel.write(trail())
      out_rel = open("ReleaseNotes_%s_%s.html" % (r[0], r[1]), "w")
      current = new_current
      out_rel.write(head())
    try:
      out_rel.write('# %s\n%s' % (r[5].encode('ascii', 'replace'), r[6].encode('ascii', 'replace')))
    except:
      pass


if __name__ == '__main__':
  getReleasesNotes()
