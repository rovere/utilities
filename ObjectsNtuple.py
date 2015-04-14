from autovars import *
import ROOT
from math import sqrt

# sip = ROOT.SignedImpactParameter()

TRACK_HITS = 0,
MISSING_INNER_HITS = 1,
MISSING_OUTER_HITS = 2


eventNTObject = NTupleObjectType("event", variables = [
        NTupleVariable("run", lambda x : x.run(), int),
        NTupleVariable("lumi", lambda x : x.luminosityBlock(), int),
        NTupleVariable("event", lambda x : x.event(), int)]
                                 )
trackNTObject = NTupleObjectType("track", variables = [
      NTupleVariable("pt", lambda *args, **kwargs : args[0].pt(), float),
      NTupleVariable("eta", lambda *args, **kwargs : args[0].eta(), float),
      NTupleVariable("phi", lambda *args, **kwargs : args[0].phi(), float),
      NTupleVariable("dxy", lambda *args, **kwargs : args[0].dxy(), float),
      NTupleVariable("dz", lambda *args, **kwargs : args[0].dz(), float),
      NTupleVariable("innerMom", lambda *args, **kwargs : sqrt(args[0].innerMomentum().x()**2 + args[0].innerMomentum().y()**2 + args[0].innerMomentum().z()**2), float),
      NTupleVariable("innerMomx", lambda *args, **kwargs : args[0].innerMomentum().x(), float),
      NTupleVariable("innerMomy", lambda *args, **kwargs : args[0].innerMomentum().y(), float),
      NTupleVariable("innerMomz", lambda *args, **kwargs : args[0].innerMomentum().z(), float),
      NTupleVariable("outerMom", lambda *args, **kwargs : sqrt(args[0].outerMomentum().x()**2 + args[0].outerMomentum().y()**2 + args[0].outerMomentum().z()**2), float),
      NTupleVariable("outerMomx", lambda *args, **kwargs : args[0].outerMomentum().x(), float),
      NTupleVariable("outerMomy", lambda *args, **kwargs : args[0].outerMomentum().y(), float),
      NTupleVariable("outerMomz", lambda *args, **kwargs : args[0].outerMomentum().z(), float),
      NTupleVariable("outerPositionx", lambda *args, **kwargs : args[0].outerPosition().x(), float),
      NTupleVariable("outerPositiony", lambda *args, **kwargs : args[0].outerPosition().y(), float),
      NTupleVariable("outerPositionz", lambda *args, **kwargs : args[0].outerPosition().z(), float),
      NTupleVariable("chi2", lambda *args, **kwargs : args[0].chi2(), float),
      NTupleVariable("algo", lambda *args, **kwargs : args[0].algo() - 4, float),
#      NTupleVariable("ip3d", lambda *args, **kwargs : sip.signedIP3D(args[0], x[1], -args[0].momentum()).value(), float),
#      NTupleVariable("sip3d", lambda *args, **kwargs : sip.signedIP3D(args[0], x[1], -args[0].momentum()).significance(), float),
      NTupleVariable("numberOfHits", lambda *args, **kwargs : args[0].hitPattern().numberOfHits(0), int),
      NTupleVariable("numberOfValidHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidHits(), int),
      NTupleVariable("numberOfTrackerHits", lambda *args, **kwargs : args[0].hitPattern().numberOfTrackerHits(0), int),
      NTupleVariable("numberOfValidTrackerHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidTrackerHits(), int),
      NTupleVariable("numberOfValidPixelHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidPixelHits(), int),
      NTupleVariable("numberOfValidPixelBarrelHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidPixelBarrelHits(), int),
      NTupleVariable("numberOfValidPixelEndcapHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidPixelEndcapHits(), int),
      NTupleVariable("numberOfValidStripHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidStripHits(), int),
      NTupleVariable("numberOfValidStripTIBHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidStripTIBHits(), int),
      NTupleVariable("numberOfValidStripTIDHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidStripTIDHits(), int),
      NTupleVariable("numberOfValidStripTOBHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidStripTOBHits(), int),
      NTupleVariable("numberOfValidStripTECHits", lambda *args, **kwargs : args[0].hitPattern().numberOfValidStripTECHits(), int),
      NTupleVariable("numberOfLostInnerHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostHits(1), int),
      NTupleVariable("numberOfLostInnerPixelHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostPixelHits(1), int),
      NTupleVariable("numberOfLostInnerPixelBarrelHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostPixelBarrelHits(1), int),
      NTupleVariable("numberOfLostInnerPixelEndcapHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostPixelEndcapHits(1), int),
      NTupleVariable("numberOfLostInnerStripHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripHits(1), int),
      NTupleVariable("numberOfLostInnerStripTIBHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTIBHits(1), int),
      NTupleVariable("numberOfLostInnerStripTIDHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTIDHits(1), int),
      NTupleVariable("numberOfLostInnerStripTOBHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTOBHits(1), int),
      NTupleVariable("numberOfLostInnerStripTECHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTECHits(1), int),
      NTupleVariable("numberOfLostOuterHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostHits(2), int),
      NTupleVariable("numberOfLostOuterPixelHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostPixelHits(2), int),
      NTupleVariable("numberOfLostOuterPixelBarrelHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostPixelBarrelHits(2), int),
      NTupleVariable("numberOfLostOuterPixelEndcapHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostPixelEndcapHits(2), int),
      NTupleVariable("numberOfLostOuterStripHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripHits(2), int),
      NTupleVariable("numberOfLostOuterStripTIBHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTIBHits(2), int),
      NTupleVariable("numberOfLostOuterStripTIDHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTIDHits(2), int),
      NTupleVariable("numberOfLostOuterStripTOBHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTOBHits(2), int),
      NTupleVariable("numberOfLostOuterStripTECHits", lambda *args, **kwargs : args[0].hitPattern().numberOfLostStripTECHits(2), int),
      NTupleVariable("loose", lambda *args, **kwargs : args[0].quality(args[0].qualityByName("loose")), int),
      NTupleVariable("tight", lambda *args, **kwargs : args[0].quality(args[0].qualityByName("tight")), int),
      NTupleVariable("highPurity", lambda *args, **kwargs : args[0].quality(args[0].qualityByName("highPurity")), int)
      ])

# For muons the main argument **MUST** be the innerTrack, since we are
# interested only in tracking aspects. The second, mandatory, argument
# is the muon object itself
muonNTObject = NTupleObjectType("muon", baseObjectTypes = [trackNTObject], variables = [
        NTupleVariable("type", lambda *args, **kwargs : args[1].type(), int)
        ])

vertexNTObject = NTupleObjectType("vertex", variables = [
        NTupleVariable("x", lambda x : x.x(), float),
        NTupleVariable("y", lambda x : x.y(), float),
        NTupleVariable("z", lambda x : x.z(), float),
        NTupleVariable("err_x", lambda x : x.xError(), float),
        NTupleVariable("err_y", lambda x : x.yError(), float),
        NTupleVariable("err_z", lambda x : x.zError(), float),
        NTupleVariable("valid", lambda x : x.isValid(), int),
        NTupleVariable("ndof", lambda x : x.ndof(), float),
        NTupleVariable("normalizedChi2", lambda x : x.normalizedChi2(), float),
        NTupleVariable("nTracks", lambda x : x.nTracks(), float)
        ])

event_vars = NTupleObject("event", eventNTObject)
track_vars = NTupleCollection("track", trackNTObject, 5000)
globalMuon_vars = NTupleCollection("muon", muonNTObject, 5000)
vertex_vars = NTupleCollection("vertex", vertexNTObject, 100)
