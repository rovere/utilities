#!/usr/bin/env python

import json
import StringIO
import pycurl
import re
import fire
from githubAPI import github_api_token
from datetime import datetime as dt
import pytz

RX_LINKS = re.compile('^Link: <(.*?)>; rel="next", <(.*?)>; rel="last"')
RX_RELEASE = re.compile('CMSSW_(\d+)_(\d+)_(\d+)(_pre[0-9]+)*(_cand[0-9]+)*(_patch[0-9]+)*')
RX_COMMIT = re.compile(".*\#(\d{0,5})( from.*)")
RX_SINGLECOMMIT = re.compile(".*cmssw/pull/(\d{0,5})")
RX_COMPARE = re.compile("(^https://github.*compare.*\.\.\..*)")

DEBUG = True

def head(title):
    ret = "---\n"
    ret += "layout: post\n"
    ret += "title:  {title}\n".format(title=title)
    ret += "date:   {now}\n".format(now=dt.now(tz=pytz.timezone('Europe/Zurich')).strftime("%Y-%m-%d %H:%M:%S %z"))
    ret += "categories: jekyll update\n"
    ret += "---\n\n"
    return ret

def extractPRnumbers(release_notes):
    prs = [re.match(RX_SINGLECOMMIT, l).group(1) for l in release_notes.split('\n') if re.match(RX_SINGLECOMMIT, l)]
    if DEBUG:
       for pr in prs:
          print "PR: ", pr
    return prs

def checkRateLimits(header):
    head = {}
    hh = [h.split(':') for h in header.split('\n')]
    for o in hh:
        if len(o) > 1:
            head.setdefault(o[0],o[1].replace('\r', ''))
    if DEBUG:
        print head
    if int(head['X-RateLimit-Remaining']) == 0:
        print "Rate Limits exceeded"
        print "X-RateLimit-Limit", head['X-RateLimit-Limit']
        print "X-RateLimit-Reset", head['X-RateLimit-Reset']
        print "X-RateLimit-Remaining", head['X-RateLimit-Remaining']
        import sys
        sys.exit(1)

def getReleasesNotes(selected_releases_regexp):
  next_link = 'first'
  last_link = 'last'
  current_link = "https://api.github.com/repos/cms-sw/cmssw/releases"
  pr_current_link = "https://api.github.com/repos/cms-sw/cmssw/pulls"
  response = StringIO.StringIO()
  pr_response = StringIO.StringIO()
  header   = StringIO.StringIO()
  pr_header   = StringIO.StringIO()
  c = pycurl.Curl()
  c.setopt(pycurl.URL, current_link)
  c.setopt(pycurl.WRITEFUNCTION, response.write)
  c.setopt(pycurl.HEADERFUNCTION, header.write)
  c.setopt(pycurl.HTTPHEADER, ['Authorization: token %s' % github_api_token])
  cpr = pycurl.Curl()
  cpr.setopt(pycurl.URL, pr_current_link)
  cpr.setopt(pycurl.WRITEFUNCTION, pr_response.write)
  cpr.setopt(pycurl.WRITEFUNCTION, pr_response.write)
  cpr.setopt(pycurl.HEADERFUNCTION, pr_header.write)
  counter = -1
  notes = []

  while next_link != last_link:
    c.perform()

    releases = json.loads(response.getvalue())
    headers = header.getvalue()
    checkRateLimits(headers)
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
      if rel_numbers and re.match(selected_releases_regexp, releases[i]['name']):
        release_notes = re.sub(RX_COMMIT, '\\n1. [\\1](http://github.com/cms-sw/cmssw/pull/\\1) \\2', releases[i]['body'])
        release_notes = re.sub(RX_COMPARE, '\\1\n\n', release_notes)
        if DEBUG:
            print release_notes
        prs = extractPRnumbers(release_notes)
        for pr in prs:
            cpr.setopt(pycurl.URL, pr_current_link + "/%s" % pr)
            cpr.setopt(pycurl.HTTPHEADER, ['Authorization: token %s' % github_api_token])
            cpr.perform()
            checkRateLimits(pr_header.getvalue())
            commit = json.loads(pr_response.getvalue())
            if commit.has_key('created_at') and commit.has_key('merged_at'):
                release_notes = re.sub('\[%s\](.*)' % pr, '[%s]\\1 created: %s merged: %s' % (pr, commit['created_at'], commit['merged_at']), release_notes)
            pr_response.seek(0)
            pr_response.truncate()
            pr_header.seek(0)
            pr_header.truncate()
        notes.append([int(rel_numbers.group(1)),
                      int(rel_numbers.group(2)),
                      int(rel_numbers.group(3)),
                      rel_numbers.group(4),
                      rel_numbers.group(5),
                      rel_numbers.group(6),
                      releases[i]['name'],
                      release_notes
                     ])
    response.seek(0)
    response.truncate()
    header.seek(0)
    header.truncate()

  current = ""
  out_rel = None
  notes = sorted(notes, key = lambda x: (x[0], x[1], x[2], x[3], x[4]), reverse=True)
  for r in notes:
    new_current = "{major}_{minor}_{subminor}".format(major=r[0],minor=r[1],subminor=r[2])
    for i in range(3,6):
        if r[i]: new_current += "{addendum}".format(addendum=r[i])
    if new_current != current:
      if out_rel:
        out_rel.close()
      out_rel = open("{date}-ReleaseNotes_{release}.md".format(date=dt.now().strftime('%Y-%m-%d'),release=new_current), 'w')
      out_rel.write(head(new_current))
      current = new_current
    try:
      out_rel.write('# %s\n%s' % (r[-2].encode('ascii', 'replace'), r[-1].encode('ascii', 'replace')))
    except:
      pass

if __name__ == '__main__':
  fire.Fire(getReleasesNotes)
