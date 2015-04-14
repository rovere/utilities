#!/usr/bin/env python

# Grab it after some lookups throu type -a eoscms/eos
EOS_COMMAND = '/afs/cern.ch/project/eos/installation/0.3.84-aquamarine/bin/eos.select'

def getFileListFromEOS(eos_repo):
  """
  Return the full list of files available under the specified eos_repo
  directory. The returned list of files includes the eos_repo as
  proper prefix of each file.
  """
  import commands
  input_files = commands.getoutput('%s ls %s' % (EOS_COMMAND, eos_repo))
  input_files = input_files.split('\n')
  input_files = map(lambda x: '%s%s' %(eos_repo, x), input_files)
  return input_files


if __name__ == '__main__':
    getFileListFrom('/store/group/phys_tracking/rovere/JetHT22Jan/JetHT/crab_JetHT_legacyJan22/150223_172317/0000/')

