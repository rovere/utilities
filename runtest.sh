#!/bin/bash

#set -o verbose

jobn=`date +%Y%m%d-%H%M%S`
config=`echo ${1} | cut -f 1 -d'.'`

OUTPUT=runtest_${config}_${jobn}.log

WORKDIR=`pwd`

echo "Starting job on " `date` &> $OUTPUT
echo "Running on " `uname -a` >> $OUTPUT 2>&1
echo "System release " `cat /etc/redhat-release` >> $OUTPUT 2>&1
echo "Current working directory: " $WORKDIR >> $OUTPUT 2>&1 

cd $CMSSW_BASE/src; eval `scram runtime -sh`; cd $WORKDIR

showtags >> $OUTPUT 2>&1

edmPluginRefresh >> $OUTPUT 2>&1

/usr/bin/time cmsRun -e -j FrameworkJobReport_${config}_${jobn}.xml -p ${1} >> $OUTPUT 2>&1

outval=$?
echo "Ending job on " `date` >> $OUTPUT 2>&1

exit ${outval}
