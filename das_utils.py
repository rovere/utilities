#!/usr/bin/env python

def getFileListFromDAS(query):
    """
    Return the result of running das_client.py --limit=0
    --query='query'. The output is returned as a list splitted by
    newline.
    """
    import commands
    files = commands.getoutput("das_client.py --limit=0 --query='%s'" % query).split('\n')
    return files

if __name__ == '__main__':
    getFileListFromDAS('file dataset=/JetHT/Run2012D-22Jan2013-v1/RECO run=208307')

