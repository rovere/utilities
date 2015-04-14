#! /bin/bash

RELEASE=$1
[ "$RELEASE" ] || exit 1

[ "$CVSROOT" ] || CVSROOT=":pserver:anonymous@cmssw.cvs.cern.ch:/local/reps/CMSSW"
HLTNAME=$(cvs -d $CVSROOT co -p -r $RELEASE Configuration/HLT/python/autoHLT.py | grep "'relval'" | cut -d"'" -f4)
[ "$HLTNAME" ] || HLTNAME="GRun"
HLTMENU=$(cvs -d $CVSROOT co -p -r $RELEASE HLTrigger/Configuration/python/HLT_${HLTNAME}_cff.py 2> /dev/null | head -n1 | cut -c 3-)
AUTOCOND=$(cvs -d $CVSROOT co -p -r $RELEASE Configuration/AlCa/python/autoCond.py)
GLOBALTAG=$(echo "$AUTOCOND" | grep "'startup'" | cut -d"'" -f4)

echo "RelVal configuration for release $RELEASE"
echo -e "HLT menu ($HLTNAME):\t$HLTMENU"
echo -e "GlobalTag (startup):\t$GLOBALTAG"

# extract any additional condition payloads
{
  echo "$AUTOCOND"
  cat << @EOF
if 'startup_$HLTNAME' in autoCond:
  for line in autoCond['startup_$HLTNAME'][1:]:
    print '\t%s' % line

@EOF
} | python

echo
