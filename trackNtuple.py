from autovars import *

trackNTObject = NTupleObjectType("track", variables = [
      NTupleVariable("pt", lambda x : x.pt(), float),
      NTupleVariable("eta", lambda x : x.eta(), float),
      NTupleVariable("phi", lambda x : x.phi(), float),
      NTupleVariable("dxy", lambda x : x.dxy(), float),
      NTupleVariable("dz", lambda x : x.dz(), float),
      NTupleVariable("ndof", lambda x : x.ndof(), float),
      NTupleVariable("chi2", lambda x : x.chi2(), float),
      NTupleVariable("algo", lambda x : x.algo() - 4, float),
      NTupleVariable("valid_sistrip", lambda x : x.hitPattern().numberOfValidStripHits(), float),
      NTupleVariable("valid_pixel", lambda x : x.hitPattern().numberOfValidPixelHits(), float),
      ])

track_vars = NTupleCollection("track", trackNTObject, 5000)
