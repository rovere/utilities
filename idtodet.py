#!/usr/bin/env python

import sys

big_det_offset = 28
medium_det_offset = 25
big_det_mask = 0xF
medium_det_mask = 0x7
layerStartBit = 14
layerMask = 0x7
ringStartBitTID = 9
ringMaskTID = 0x3
ringStartBitTEC = 5
ringMaskTEC = 0x7
PB_Offset = 16
PB_Mask =  0xF
PE_Offset = 23
PE_Mask =  0x3
TIB_Offset = 14
TIB_Mask =  0x7
TOB_Offset = 14
TOB_Mask =  0x7
TEC_sideStartBit = 18
TEC_sideMask = 0x3
TEC_wheelStartBit = 14
TEC_wheelMask = 0xf

big_dets = ['Tracker', 'Muon', 'Ecal', 'Hcal', 'Calo']
medium_dets = ['Unknown', 'PB','PE',
               'TIB', 'TID', 'TOB', 'TEC']
module_dets = ['UNKNOWNGEOMETRY', 'IB1', 'IB2', 'OB1', 'OB2', 'W1A', 'W2A', 'W3A', 'W1B', 'W2B', 'W3B', 'W4', 'W5', 'W6', 'W7']


def glued(id):
    if ((id>>0) & 0x3) == 1:
        return id - 1
    elif ((id>>0) & 0x3) == 2:
        return id - 2
    else:
        return 0

def stereo(id):
    if ((id>>0 ) & 0x3 ) == 1:
        return ((id>>0) & 0x3)
    else:
        return 0

def partnerId(id):
    if ((id>>0) & 0x3) == 1:
        return id + 1
    elif ((id>>0) & 0x3) == 2:
        return id - 1
    else:
        return 0

def id2det(id):
    big_structure = big_dets[id>>big_det_offset&big_det_mask - 1]
    print "RAW ID: %d" % id
    print "Biggest Structure is %s" % big_structure
    if big_structure == 'Tracker':
        medium_structure = medium_dets[id>>medium_det_offset&medium_det_mask]
        print medium_structure
        if medium_structure == 'TIB':
            print "Layer %d" % int((id>>TIB_Offset) & TIB_Mask) 
        if medium_structure == 'TOB':
            print "Layer %d" % int((id>>TOB_Offset) & TOB_Mask) 
        if medium_structure == 'TID':
            ring_id = (id>>9) & 0x3
            print 'ring: %d' % ring_id
            side = int((id>>13) & 0x3)
            print "Side: %d (1:neg 2:plus) " % side
            wheel = int((id>>11) & 0x3)
            isDoubleSide = (glued(id) == 0 and ( ring_id == 1 or ring_id == 2 ))
            print "DiskNumber: %d" % wheel
            print "isDoubleSide: %d" % isDoubleSide
            print "Stereo: %d (0:Not Stereo, !0:Stereo)" % stereo(id)
            print "Glued: %d  (0:Not glued, !0:Glued)" % glued(id)
            isRPhi = (stereo(id) == 0 and not isDoubleSide)
            print "isRPhi: %d" % isRPhi
            print "PartnerId: %d" % partnerId(id)
        if medium_structure == 'TEC':
            ring_id = (id>>ringStartBitTEC) & ringMaskTEC
            print 'ring: %d' % ring_id
            side = (id>>TEC_sideStartBit) & TEC_sideMask
            print "Side: %d (1:neg 2:plus) " % side
            wheel = (id>>TEC_wheelStartBit & TEC_wheelMask)
            print "Wheel: %d" % wheel
            print "isDoubleSide: %d" % (glued(id) == 0 and ( ring_id == 1 or ring_id == 2 or ring_id == 5 ))
            print "Glued: %d (0:Not glued, !0:Glued)" % glued(id) 
            print "PartnerId: %d" % partnerId(id)
        if medium_structure == 'PB':
            print "Layer %d" % int((id>>PB_Offset) & PB_Mask) 

def id2det2String(id):
    ret = '%d ' % id
    big_structure = big_dets[id>>big_det_offset&big_det_mask - 1]
    if big_structure == 'Tracker':
        medium_structure = medium_dets[id>>medium_det_offset&medium_det_mask]
        ret += " %s" % medium_structure
        if medium_structure == 'TIB':
            ret += " %d" % int((id>>TIB_Offset) & TIB_Mask) 
        if medium_structure == 'TOB':
            ret += " %d" % int((id>>TOB_Offset) & TOB_Mask) 
        if medium_structure == 'TID':
            ring_id = (id>>9) & 0x3
            ret += ' ring: %d' % ring_id
            side = int((id>>13) & 0x3)
            ret += " Side: %d (1:neg 2:plus) " % side
            wheel = int((id>>11) & 0x3)
            isDoubleSide = (glued(id) == 0 and ( ring_id == 1 or ring_id == 2 ))
            ret += " DiskNumber: %d" % wheel
            ret += " isDoubleSide: %d" % isDoubleSide
            ret += " Stereo: %d (0:Not Stereo, !0:Stereo)" % stereo(id)
            ret += " Glued: %d  (0:Not glued, !0:Glued)" % glued(id)
            isRPhi = (stereo(id) == 0 and not isDoubleSide)
            ret += " isRPhi: %d" % isRPhi
            ret += " PartnerId: %d" % partnerId(id)
        if medium_structure == 'TEC':
            ring_id = (id>>ringStartBitTEC) & ringMaskTEC
            ret += ' ring: %d' % ring_id
            side = (id>>TEC_sideStartBit) & TEC_sideMask
            ret += " Side: %d (1:neg 2:plus) " % side
            wheel = (id>>TEC_wheelStartBit & TEC_wheelMask)
            ret += " Wheel: %d" % wheel
            ret += " isDoubleSide: %d" % (glued(id) == 0 and ( ring_id == 1 or ring_id == 2 or ring_id == 5 ))
            ret += " Glued: %d (0:Not glued, !0:Glued)" % glued(id) 
            ret += " PartnerId: %d" % partnerId(id)
        if medium_structure == 'PB':
            ret += " Layer %d" % int((id>>PB_Offset) & PB_Mask) 
    return ret

if __name__ == '__main__':
  if len(sys.argv) < 2:
    print "Error. Usage %s id\n.Quitting\n" % sys.argv[0]
  id2det(int(sys.argv[1]))
