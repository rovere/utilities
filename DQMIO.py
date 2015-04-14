#!/bin/env python

"""Package responsible for browsing the content of a DQM file produced
  with the DQMIO I/O framework of CMSSW. The internal format of the
  DQMIO file is the following: it has one TTree for each kind of
  object that can be handled by the DQM Framework. Each entry in these
  TTree has a pointer to the ROOT object (Value), the path information
  (FullName) and the flags info (Flag). Entries in these TTres are
  referenced by their cardinal/numerical order. An additional index
  TTree is saved in order to be able to associate entries in the
  previous TTrees to Run/LS information. The index TTree is fairly
  simple: it has one entry for each kind of product we need to save,
  either run or lumi product, and 2 indiced: first_index and
  last_index(inclusive), that are pointing to the TTrees that hold the
  histogram information and represent the total amount of histograms,
  in the form or range-of-entries that are bound to the specific
  Run/LS. In order to decode the file we need to query the index TTree
  first and then look for the appropriate histograms in the correct
  range in the proper TTree, depending on the kind of histograms we
  are looking for."""

__author__ = "Marco Rovere"
__version__ = '1.0.0'

import ROOT as R
import sys
import re
import os


class DQMIO:

  """Class responsible for browsing the content of a DQM file produced
  with the DQMIO I/O framework of CMSSW."""

  types=["Ints","Floats","Strings",
         "TH1Fs","TH1Ss","TH1Ds",
         "TH2Fs", "TH2Ss", "TH2Ds",
         "TH3Fs", "TProfiles","TProfile2Ds", "kNIndicies"]

  def __init__(self, filename):
    self._filename = filename
    self._canvas = None
    if os.path.exists(self._filename):
      self._root_file = R.TFile.Open(self._filename)
    else:
      print "File %s does not exists" % self._filename
      sys.exit(1)
  
  def _check_type(self, type):
    if type not in DQMIO.types:
      print "Type %s is not supported: ignoring." % type
      return False
    return True
    
  def print_index(self):

    """Loop over the complete index and dump it on the screen."""
    
    indices = self._root_file.Get("Indices")
    print "Run,\tLumi,\tType,\t\tFirstIndex,\tLastIndex"
    for i in xrange(indices.GetEntries()):
      indices.GetEntry(i)
      if indices.Type > len(DQMIO.types):
        print '{0:4d}\t{1:4d}\t{2:4d}({3:s})\t\t{4:4d}\t{5:4d}'.format(indices.Run,\
                                                                       indices.Lumi,\
                                                                       indices.Type,\
                                                                       'Unkwn',\
                                                                       indices.FirstIndex,\
                                                                       indices.LastIndex)
      else:
        print '{0:4d}\t{1:4d}\t{2:4d}({3:s})\t\t{4:4d}\t{5:4d}'.format(indices.Run,\
                                                                       indices.Lumi,\
                                                                       indices.Type,\
                                                                       DQMIO.types[indices.Type],\
                                                                       indices.FirstIndex,\
                                                                       indices.LastIndex)

  def print_histo_names(self, types, index_range, regex=None):

    """Given a list of types of histograms in input and a single
    range, look into the appropriate TTree and print the names of all
    the histograms in that range. The list of registered types is
    stored in DQMIO.types."""
    
    for type in types:
      if self._check_type(type):
        print 'Histograms of type %s' % type
        t_tree = self._root_file.Get(type)
        for i in range(0, t_tree.GetEntries()+1):
          t_tree.GetEntry(i)
          if i >= index_range[0] and i <= index_range[1]:
            if regex:
              if re.match(regex, str(t_tree.FullName)):
                print 'Name: %s, index: %i' % (t_tree.FullName, i)
            else:
                print 'Name: %s, index: %i' % (t_tree.FullName, i)


  def draw_plot(self, type, histo_fullname, same=False):

    """Given a type of histogram and its full pathname, draw it on the
    Canvas. Note that this method will try to draw _all_ the
    histograms that match the given full pathname, exploring all
    possible ranges registered in the current file. User is prompt to
    quit the loop after each matching histogram has been drawn. """

    if not self._canvas:
      print 'Creating new canvas'
      self._canvas = R.TCanvas('canvas_%s' % self._filename,
                               'canvas_%s' % self._filename, 800, 800)
    if self._check_type(type):
      t_tree = self._root_file.Get(type)
      for i in range(0, t_tree.GetEntries()+1):
        t_tree.GetEntry(i)
        if t_tree.FullName == histo_fullname:
          if same:
            t_tree.Value.Draw("SAME")
          else:
            t_tree.Value.Draw()            
          self._canvas.Update()
          c = raw_input("[%d] Another one? " % i)
          if c not in ['y', 'yes', 'Y']:
            break

      
if __name__ == '__main__':
  filename = sys.argv[1]
  dqmio = DQMIO(filename)
  dqmio.print_index()
  if len(sys.argv) > 2:
    dqmio.draw_plot(sys.argv[2], sys.argv[3])
