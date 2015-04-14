#!/usr/bin/env python

import sys
import re

def generateFilename(prefix, file_count, suffix):
    return "%s_%04d.%s" % (prefix, file_count, suffix)

def split(filename, prefix, suffix, regexp, do_html, frequency=1):
    file_count = 0
    count = 0
    f = open(filename,'r')
    o = open(generateFilename(prefix, file_count, suffix), 'w')
    for line in f:
        g = re.match(regexp, line)
        if g:
            count += 1
        if count > 1 and (count%int(frequency) == 0):
            o.close()
            sys.stdout.write('.')
            sys.stdout.flush()
            file_count += 1
            if file_count%10 == 0:
                sys.stdout.write('\n')
                sys.stdout.flush()
            count = 0
            o = open(generateFilename(prefix, file_count, suffix), 'w')
        if g and do_html:
            try:
                o.write('<div id=%s> <a href="%s#%s">%s</a> %s </div>\n' % (g.group(1),
                                                                            generateFilename(prefix, file_count, suffix),
                                                                            g.group(1).replace('"', ''),
                                                                            g.group(1),
                                                                            line.rstrip()))
            except:
                o.write(line)
        else:
            o.write(line)
    sys.stdout.write('\n')
    sys.stdout.flush()

if __name__ == '__main__':
    from optparse import OptionParser
    
    usage = "usage: %prog [options] filename"
    opt = OptionParser(usage=usage)

    
    opt.add_option("-p", "--prefix", dest="prefix", metavar="SUFFIX", default="xx",
                   help="Prefix for the output filenames [default: %default].")
    opt.add_option("-s", "--suffix", dest="suffix", metavar="SUFFIX", default="txt",
                   help="Suffix for the output filenames, _not_ including the '.' [default: %default].")
    opt.add_option("-r", "--regexp", dest="regexp", metavar="REGEXP", default="\n",
                   help="Regular expression used to split the file [default: %default].")
    opt.add_option("-f", "--frquency", dest="frequency", metavar="FREQ", default=1000, type=int,
                   help="Frequency with which the input file will be split upon REGEXP matching [default: %default].")
    opt.add_option("-H", "--html", dest="do_html", default=False, action="store_true",
                   help="Add HTML tags around the matched regexp, like <div id='matched regexp'>full lines</div>")
    opts, args = opt.parse_args()
    if len(args) == 0:
        print >> sys.stderr, sys.argv[0], \
              ": split.py [options] filename"
        sys.exit(1)
    split(args[0], opts.prefix, opts.suffix, opts.regexp, opts.do_html, opts.frequency)
    
