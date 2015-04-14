#include <vector>

#include <iostream>
#include <ostream>

#include <stdint.h>
/** \class DetId

Parent class for all detector ids in CMS.  The DetId is a 32-bit
unsigned integer.  The four most significant bits ([31:28]) identify
the large-scale detector (e.g. Tracker or Ecal) while the next three
bits ([27:25]) identify a part of the detector (such as HcalBarrel
(HB) for Hcal).

*/
class DetId {
public:
  static const int kDetOffset          = 28;
  static const int kSubdetOffset       = 25;


  enum Detector { Tracker=1,Muon=2,Ecal=3,Hcal=4,Calo=5 };
  /// Create an empty or null id (also for persistence)
  DetId()  : id_(0) { }
  /// Create an id from a raw number
  DetId(uint32_t id) : id_(id) { }
  /// Create an id, filling the detector and subdetector fields as specified
  DetId(Detector det, int subdet)  {
    id_=((det&0xF)<<28)|((subdet&0x7)<<25);
  }

  /// get the detector field from this detid
  Detector det() const { return Detector((id_>>kDetOffset)&0xF); }
  /// get the contents of the subdetector field (not cast into any detector's numbering enum)
  int subdetId() const { return ((id_>>kSubdetOffset)&0x7); }

  uint32_t operator()() const { return id_; }
  operator uint32_t() const { return id_; }

  /// get the raw id 
  uint32_t rawId() const { return id_; }
  /// is this a null id ?
  bool null() const { return id_==0; }
  
  /// equality
  bool operator==(DetId id) const { return id_==id.id_; }
  /// inequality
  bool operator!=(DetId id) const { return id_!=id.id_; }
  /// comparison
  bool operator<(DetId id) const { return id_<id.id_; }

protected:
  uint32_t id_;
};

/// equality
inline bool operator==(uint32_t i, DetId id)  { return i==id(); }
inline bool operator==(DetId id, uint32_t i)  { return i==id(); }
/// inequality
inline bool operator!=(uint32_t i, DetId id)  { return i!=id(); }
inline bool operator!=(DetId id, uint32_t i) { return i!=id(); }
/// comparison
inline bool operator<(uint32_t i, DetId id) { return i<id(); }
inline bool operator<(DetId id, uint32_t i) { return id()<i; }


class SiStripDetId;

/** Debug info for SiStripDetId class. */
std::ostream& operator<< ( std::ostream&, const SiStripDetId& );

/** 
    @class SiStripDetId
    @author R.Bainbridge
    @brief Detector identifier class for the strip tracker.
*/
class SiStripDetId : public DetId {
  
 public:

  // ---------- Constructors, enumerated types ----------
  
  /** Construct a null id */
  SiStripDetId()  : DetId() {;}

  /** Construct from a raw value */
  SiStripDetId( const uint32_t& raw_id ) : DetId( raw_id ) {;}

  /** Construct from generic DetId */
  SiStripDetId( const DetId& det_id )  : DetId( det_id.rawId() ) {;}

  /** Construct and fill only the det and sub-det fields. */
  SiStripDetId( Detector det, int subdet ) : DetId( det, subdet ) {;}

  /** Enumerated type for tracker sub-deteector systems. */
  enum SubDetector { UNKNOWN=0, TIB=3, TID=4, TOB=5, TEC=6 };
  
  /** Enumerated type for tracker module geometries. */
  enum ModuleGeometry {UNKNOWNGEOMETRY, IB1, IB2, OB1, OB2, W1A, W2A, W3A, W1B, W2B, W3B, W4, W5, W6, W7};

  // ---------- Common methods ----------

  /** Returns enumerated type specifying sub-detector. */
  inline SubDetector subDetector() const;
  
  /** Returns enumerated type specifying sub-detector. */
  inline ModuleGeometry moduleGeometry() const;

  /** A non-zero value means a glued module, null means not glued. */
  inline uint32_t glued() const;
  
  /** A non-zero value means a stereo module, null means not stereo. */
  inline uint32_t stereo() const;

  /** Returns DetId of the partner module if glued, otherwise null. */
  inline uint32_t partnerDetId() const;
 
  /** Returns strip length of strip tracker sensor, otherwise null. */
  inline double stripLength() const;
  
  
  // ---------- Constructors that set "reserved" field ----------
  
  /** Construct from a raw value and set "reserved" field. */
  SiStripDetId( const uint32_t& raw_id, 
		const uint16_t& reserved )
    : DetId( raw_id ) 
  {
    id_ &= ( ~static_cast<uint32_t>(reservedMask_<<reservedStartBit_) );
    id_ |= ( ( reserved & reservedMask_ ) << reservedStartBit_ );
  }
  
  // -----------------------------------------------------------------------------
  //
  
  /** Construct from generic DetId and set "reserved" field. */
  SiStripDetId( const DetId& det_id, 
		const uint16_t& reserved )
    : DetId( det_id.rawId() ) 
  {
    id_ &= ( ~static_cast<uint32_t>(reservedMask_<<reservedStartBit_) );
    id_ |= ( ( reserved & reservedMask_ ) << reservedStartBit_ );
  }

  
  /** Returns value of "reserved" field. */
  inline uint16_t reserved() const;
  
private:
  
  /** Position of "reserved" bit field. */ 
  static const uint16_t reservedStartBit_ = 20;
  
  /** */
  static const uint32_t sterStartBit_ = 0;

  /** Mask for "reserved" bit field (3-bits wide). */ 
  static const uint16_t reservedMask_ = 0x7;

  /** */
  static const uint32_t sterMask_ = 0x3;

  static const unsigned layerStartBit_ = 14;
  static const unsigned layerMask_ = 0x7;
  static const unsigned ringStartBitTID_= 9;
  static const unsigned ringMaskTID_= 0x3;
  static const unsigned ringStartBitTEC_= 5;
  static const unsigned ringMaskTEC_= 0x7;
  
};

// ---------- inline methods ----------

SiStripDetId::SubDetector SiStripDetId::subDetector() const {
  if( det() == DetId::Tracker &&
      subdetId() == static_cast<int>(SiStripDetId::TIB) ) {
    return SiStripDetId::TIB;
  } else if ( det() == DetId::Tracker &&
	      subdetId() == static_cast<int>(SiStripDetId::TID) ) {
    return SiStripDetId::TID;
  } else if ( det() == DetId::Tracker &&
	      subdetId() == static_cast<int>(SiStripDetId::TOB) ) {
    return SiStripDetId::TOB;
  } else if ( det() == DetId::Tracker &&
	      subdetId() == static_cast<int>(SiStripDetId::TEC) ) {
    return SiStripDetId::TEC;
  } else {
    return SiStripDetId::UNKNOWN;
  }
}

SiStripDetId::ModuleGeometry SiStripDetId::moduleGeometry() const {
  switch(subDetector()) {
  case TIB: return int((id_>>layerStartBit_) & layerMask_)<3? IB1 : IB2;
  case TOB: return int((id_>>layerStartBit_) & layerMask_)<5? OB2 : OB1;
  case TID: switch ((id_>>ringStartBitTID_) & ringMaskTID_) {
    case 1: return W1A;
    case 2: return W2A;
    case 3: return W3A;
    }
  case TEC: switch ((id_>>ringStartBitTEC_) & ringMaskTEC_) {
    case 1: return W1B;
    case 2: return W2B;
    case 3: return W3B;
    case 4: return W4;
    case 5: return W5;
    case 6: return W6;
    case 7: return W7;
    }
  case UNKNOWN: default: return UNKNOWNGEOMETRY;
  }
}

uint32_t SiStripDetId::glued() const {
  if ( ((id_>>sterStartBit_) & sterMask_ ) == 1 ) {
    return ( id_ - 1 );
  } else if ( ((id_>>sterStartBit_) & sterMask_ ) == 2 ) {
    return ( id_ - 2 );
  } else { return 0; }
}
 
uint32_t SiStripDetId::stereo() const {
  if ( ((id_>>sterStartBit_ ) & sterMask_ ) == 1 ) {
    return ( (id_>>sterStartBit_) & sterMask_ );
  } else { return 0; }
}
 
uint32_t SiStripDetId::partnerDetId() const {
  if ( ((id_>>sterStartBit_) & sterMask_ ) == 1 ) {
    return ( id_ + 1 );
  } else if ( ((id_>>sterStartBit_) & sterMask_ ) == 2 ) {
    return ( id_ - 1 );
  } else { return 0; }
}
 
double SiStripDetId::stripLength() const {
  return 0.;
}


uint16_t SiStripDetId::reserved() const { 
  return static_cast<uint16_t>( (id_>>reservedStartBit_) & reservedMask_ );
}

/** 
 *  Enumeration for Strip Tracker Subdetectors
 *
 */


class StripSubdetector :public DetId { 
 public:
 enum SubDetector { TIB=3,TID=4,TOB=5,TEC=6 };
 
 /** Constructor from a raw value */
 StripSubdetector(uint32_t rawid) : DetId(rawid) {}
 /**Construct from generic DetId */
 StripSubdetector(const DetId& id) : DetId(id) {}
 
 
 /// glued
 /**
  * glued() = 0 it's not a glued module
  * glued() != 0 it's a glued module
  */
 unsigned int glued() const
   {
     if(((id_>>sterStartBit_)& sterMask_) == 1){
       return (id_ -1);
     }else if(((id_>>sterStartBit_)& sterMask_) == 2){
       return (id_ -2);
     }else{
       return 0;
     }
   }
 
 /// stereo 
 /**
  * stereo() = 0 it's not a stereo module
  * stereo() = 1 it's a stereo module
  */
 unsigned int stereo() const 
   {
     if(((id_>>sterStartBit_)& sterMask_)==1){
       return ((id_>>sterStartBit_)& sterMask_);
     }else{
       return 0;
     }
   }
 
 /**
  * If the DetId identify a glued module return 
  * the DetId of your partner otherwise return 0
  */
 
 unsigned int partnerDetId() const
   {
     if(((id_>>sterStartBit_)& sterMask_)==1){
       return (id_ + 1);
     }else if(((id_>>sterStartBit_)& sterMask_)==2){
       return (id_ - 1);
     }else{
       return 0;
     }
   }
 
 private:
 static const unsigned int detStartBit_=       2;
 static const unsigned int sterStartBit_=      0;
 
 static const unsigned int detMask_=           0x3;
 static const unsigned int sterMask_=          0x3;
 
 
};

/** 
 * Det identifier class for the TIB
 */
class TIDDetId;

std::ostream& operator<<(std::ostream& os,const TIDDetId& id);

class TIDDetId : public SiStripDetId {
 public:
  /** Constructor of a null id */
  TIDDetId();
  /** Constructor from a raw value */
  TIDDetId(uint32_t rawid);
  /**Construct from generic DetId */
  TIDDetId(const DetId& id); 
  
  TIDDetId(uint32_t side,
	   uint32_t wheel,
	   uint32_t ring,
	   uint32_t module_fw_bw,
	   uint32_t module,
	   uint32_t ster) : SiStripDetId(DetId::Tracker,StripSubdetector::TID){
    id_ |= (side& sideMask_)      << sideStartBit_    |
      (wheel& wheelMask_)          << wheelStartBit_      |
      (ring& ringMask_)            << ringStartBit_       |
      (module_fw_bw& module_fw_bwMask_)  << module_fw_bwStartBit_  |
      (module& moduleMask_)              << moduleStartBit_        |
      (ster& sterMask_)            << sterStartBit_ ;
  }
  
  
  /// positive or negative id
  /**
   * side() = 1 The DetId identify a module in the negative part
   * side() = 2 The DetId identify a module in the positive part
   */
  unsigned int side() const{
    return int((id_>>sideStartBit_) & sideMask_);
  }
  
  /// wheel id
  unsigned int wheel() const{
    return int((id_>>wheelStartBit_) & wheelMask_);
  }
  
  ///ring id
  unsigned int ring() const
    { return ((id_>>ringStartBit_) & ringMask_) ;}
  
  /// det id
  /**
   * vector[0] = 1 -> back ring
   * vector[0] = 2 -> front ring
   * vector[1] -> module
   */
  std::vector<unsigned int> module() const
    { std::vector<unsigned int> num;
      num.push_back( order() );
      num.push_back( moduleNumber() );
      return num ;}
  
  unsigned int order() const 
  { return ((id_>>module_fw_bwStartBit_) & module_fw_bwMask_);}

  /** Returns true if the module is a double side = rphi + stereo */
  bool isDoubleSide() const;
  
  /** Returns true if the module is in TID+ (z>0 side) */
  bool isZPlusSide() const
  { return (!isZMinusSide());}
  
  /** Returns true if the module is in TID- (z<0 side) */
  bool isZMinusSide() const
  { return (side()==1);}
  
  /** Returns true if the ring is mounted on the disk back (not facing impact point) */
  bool isBackRing() const
  { return (order()==1);}
  
  /** Returns true if the ring is mounted on the disk front (facing impact point) */
  bool isFrontRing() const
  { return (!isBackRing());}
  
  /** Returns the disk number */
  unsigned int diskNumber() const
  { return wheel();}
  
  /** Returns the ring number */
  unsigned int ringNumber() const
  { return ring();}
  
  /** Returns the module number */
  unsigned int moduleNumber() const
  { return ((id_>>moduleStartBit_) & moduleMask_);}
  
  /** Returns true if the module is rphi */
  bool isRPhi()
  { return (stereo() == 0 && !isDoubleSide());}
  
  /** Returns true if the module is stereo */
  bool isStereo()
  { return (stereo() != 0 && !isDoubleSide());}
  
private:
  /// two bits would be enough, but  we could use the number "0" as a wildcard
  static const unsigned int sideStartBit_=          13;
  static const unsigned int wheelStartBit_=         11;
  static const unsigned int ringStartBit_=          9;
  static const unsigned int module_fw_bwStartBit_=  7;
  static const unsigned int moduleStartBit_=        2;
  static const unsigned int sterStartBit_=          0;
  /// two bits would be enough, but  we could use the number "0" as a wildcard
  static const unsigned int sideMask_=           0x3;
  static const unsigned int wheelMask_=          0x3;
  static const unsigned int ringMask_=           0x3;
  static const unsigned int module_fw_bwMask_=   0x3;
  static const unsigned int moduleMask_=         0x1F;
  static const unsigned int sterMask_=           0x3;
};


inline
TIDDetId::TIDDetId() : SiStripDetId() {
}
inline
TIDDetId::TIDDetId(uint32_t rawid) : SiStripDetId(rawid) {
}
inline
TIDDetId::TIDDetId(const DetId& id) : SiStripDetId(id.rawId()) {
}
inline
bool TIDDetId::isDoubleSide() const {
  // Double Side: only rings 1 and 2
  return this->glued() == 0 && ( this->ring() == 1 || this->ring() == 2 );
}

/** 
 *  Det identifier class for the TEC
 */
class TECDetId;

std::ostream& operator<<(std::ostream& s,const TECDetId& id);

class TECDetId : public SiStripDetId {
 public:
  /** Constructor of a null id */
  TECDetId();
  /** Constructor from a raw value */
  TECDetId(uint32_t rawid);
  /**Construct from generic DetId */
  TECDetId(const DetId& id); 
  
  TECDetId(uint32_t side,
	   uint32_t wheel,
	   uint32_t petal_fw_bw,
	   uint32_t petal,
	   uint32_t ring,
	   uint32_t module,
	   uint32_t ster) : SiStripDetId(DetId::Tracker,StripSubdetector::TEC){
    id_ |= (side& sideMask_)         << sideStartBit_ |
      (wheel& wheelMask_)             << wheelStartBit_ |
      (petal_fw_bw& petal_fw_bwMask_) << petal_fw_bwStartBit_ |
      (petal& petalMask_)             << petalStartBit_ |
      (ring& ringMask_)               << ringStartBit_ |
      (module& moduleMask_)                 << moduleStartBit_ |
      (ster& sterMask_)               << sterStartBit_ ;
  }
  
  
  /// positive or negative id
  /**
   * side() = 1 The DetId identify a module in the negative part (TEC-)
   * side() = 2 The DetId identify a module in the positive part (TEC+)
   */
  unsigned int side() const{
    return int((id_>>sideStartBit_) & sideMask_);
  }
  
  /// wheel id
  unsigned int wheel() const
    { return ((id_>>wheelStartBit_) & wheelMask_) ;}
  
  /// petal id
  /**
   * vector[0] = 1 -> back petal
   * vector[0] = 2 -> front petal
   * vector[1] -> petal
   */
  std::vector<unsigned int> petal() const
    { std::vector<unsigned int> num;
      num.push_back(order());
      num.push_back(petalNumber());
      return num ;}
  
  unsigned int order() const
  { return ((id_>>petal_fw_bwStartBit_) & petal_fw_bwMask_);}

  /// ring id
  unsigned int ring() const
    { return ((id_>>ringStartBit_) & ringMask_) ;}
  
  /// det id
  unsigned int module() const
    { return ((id_>>moduleStartBit_) & moduleMask_);}
  
  /** Returns true if the module is a double side = rphi + stereo */
  bool isDoubleSide() const;
  
  /** Returns true if the module is in TEC+ (z>0 side) */
  bool isZPlusSide() const
  { return (!isZMinusSide());}
  
  /** Returns true if the module is in TEC- (z<0 side) */
  bool isZMinusSide() const
  { return (side()==1);}
  
  /** Returns the wheel number */
  unsigned int wheelNumber() const
  { return wheel();}
  
  /** Returns the petal number */
  unsigned int petalNumber() const
  { return ((id_>>petalStartBit_) & petalMask_);}
  
  /** Returns the ring number */
  unsigned int ringNumber() const
  { return ring();}
  
  /** Returns the module number */
  unsigned int moduleNumber() const
  { return module();}
  
  /** Returns true if the petal is mounted on the wheel back (not facing impact point) */
  bool isBackPetal() const
  { return (order()==1);}
  
  /** Returns true if the petal is mounted on the wheel front (facing impact point) */
  bool isFrontPetal() const
  { return (!isBackPetal());}
  
  /** Returns true if the module is rphi */
  bool isRPhi()
  { return (stereo() == 0 && !isDoubleSide());}
  
  /** Returns true if the module is stereo */
  bool isStereo()
  { return (stereo() != 0 && !isDoubleSide());}
  
private:
  /// two bits would be enough, but  we could use the number "0" as a wildcard
  static const unsigned int sideStartBit_=           18;
  static const unsigned int wheelStartBit_=          14;  
  static const unsigned int petal_fw_bwStartBit_=    12;
  static const unsigned int petalStartBit_=          8;
  static const unsigned int ringStartBit_=           5;
  static const unsigned int moduleStartBit_=         2;
  static const unsigned int sterStartBit_=           0;
  /// two bits would be enough, but  we could use the number "0" as a wildcard
  static const unsigned int sideMask_=          0x3;
  static const unsigned int wheelMask_=         0xF;
  static const unsigned int petal_fw_bwMask_=   0x3;
  static const unsigned int petalMask_=         0xF;
  static const unsigned int ringMask_=          0x7;
  static const unsigned int moduleMask_=        0x7;
  static const unsigned int sterMask_=          0x3;
};


inline
TECDetId::TECDetId() : SiStripDetId() {
}
inline
TECDetId::TECDetId(uint32_t rawid) : SiStripDetId(rawid) {
}
inline
TECDetId::TECDetId(const DetId& id) : SiStripDetId(id.rawId()){
}

inline
bool TECDetId::isDoubleSide() const {
  // Double Side: only rings 1, 2 and 5
  return this->glued() == 0 && ( this->ring() == 1 || this->ring() == 2 || this->ring() == 5 ) ;
}


int main() {
  TECDetId aTec(470377546);
  TIDDetId aTid(402672274);

  std::cout << aTec << std::endl;
  std::cout << aTid << std::endl;

  return 0;
}

std::ostream& operator<<(std::ostream& os,const TECDetId& id) {
  unsigned int              theWheel  = id.wheel();
  unsigned int              theModule = id.module();
  std::vector<unsigned int> thePetal  = id.petal();
  unsigned int              theRing   = id.ring();
  std::string side;
  std::string petal;
  side  = (id.side() == 1 ) ? "-" : "+";
  petal = (thePetal[0] == 1 ) ? "back" : "front";
  std::string type;
  type = (id.stereo() == 0) ? "r-phi" : "stereo";
  type = (id.glued() == 0) ? type : type+" glued";
  type = (id.isDoubleSide()) ? "double side" : type;
  return os << "TEC" << side
	    << " Wheel " << theWheel
      	    << " Petal " << thePetal[1] << " " << petal
	    << " Ring " << theRing
	    << " Module " << theModule << " " << type
	    << " (" << id.rawId() << ")";
}

std::ostream& operator<<(std::ostream& os,const TIDDetId& id) {
  unsigned int         theDisk   = id.wheel();
  unsigned int         theRing   = id.ring();
  std::vector<unsigned int> theModule = id.module();
  std::string side;
  std::string part;
  side = (id.side() == 1 ) ? "-" : "+";
  part = (theModule[0] == 1 ) ? "back" : "front";
  std::string type;
  type = (id.stereo() == 0) ? "r-phi" : "stereo";
  type = (id.glued() == 0) ? type : type+" glued";
  type = (id.isDoubleSide()) ? "double side" : type;
  return os << "TID" << side
	    << " Disk " << theDisk
	    << " Ring " << theRing << " " << part
	    << " Module " << theModule[1] << " " << type
	    << " (" << id.rawId() << ")";
}






