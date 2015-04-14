#!/usr/bin/env python
import json
import sys


def merge_intervals(intervals):
    if not intervals:
        return []
    intervals = sorted(intervals, key = lambda x: x[0])
    result = []
    (a, b) = intervals[0]
    for (x, y) in intervals[1:]:
        if x <= b:
            b = max(b, y)
        else:
            result.append([a, b])
            (a, b) = (x, y)
    result.append([a, b])
    return result

def invert_intervals(intervals,min_val=1,max_val=9999):
    # first order and merge in case
    if not intervals:
        return []
    intervals=merge_intervals(intervals)
    intervals = sorted(intervals, key = lambda x: x[0])
    result = []
    if min_val==-1:
        # defin min and max
        (a,b)=intervals[0]
        min_val=a
    if max_val==-1:
        (a,b)=intervals[len(intervals)-1]
        max_val=b

    curr_min=min_val
    for (x,y) in intervals:
        if x>curr_min:
            result.append([curr_min,x-1])
        curr_min=y+1
    if curr_min<max_val:
        result.append([curr_min,max_val])

#    print min_val,max_val
    return result



def sortByRun(adict):
    runs = adict.keys()
    runs.sort()
    for r in runs:
        yield [r, adict[r]]

if len(sys.argv) < 2:
    print "USAGE:\n", sys.argv[0], " json_file [Validation_json_file_to_merge]"
    sys.exit(1)

f = open(sys.argv[1], "r")
content = ''
for line in f:
    content += line
decode = json.loads(content)
f.close()

merge = 0
try:
    f = open(sys.argv[2], "r")
    contentMerge = ''
    for line in f:
        contentMerge += line
    decodeMerge = json.loads(contentMerge)
    f.close()
    merge = 1
except:
    pass

totalLumi = 0
for run,lumi in sortByRun(decode):
    print "Run: ", run, " Lumis: ", lumi#, " Inv Lumi: ", invert_intervals(lumi)
    ll = eval(str(lumi))
    for k in lumi:
        totalLumi += k[1] - k[0] + 1
print "Total Lumi: ", totalLumi

if merge == 1:
    f = open('MergedJson.json', 'w')
    f.write("{")
    jsonString = ''
    print 'After MERGE'
    for runVal, lumiVal in sortByRun(decodeMerge):
        for run,lumi in sortByRun(decode):
#            print 'Examining Run', run
            if run == runVal:
                jsonString += '"'+run+'":'
                # do the actual mering
                lumis = []
                for k in invert_intervals(lumi):
                    lumis.append(k)
                for k in invert_intervals(lumiVal):
                    lumis.append(k)
#                print lumis
                lumis=merge_intervals(lumis)
                lumis=invert_intervals(lumis)
                jsonString += str(lumis) + ','
                print "Run: ", run, " Lumis: ", lumis
    jsonString = jsonString.rstrip(',')
    f.write(jsonString)
    f.write("}\n")
    f.close()
