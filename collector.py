#!/usr/bin/env python

import socket
import select
import struct
import ROOT
from io import BytesIO as bio
from  time import sleep
from random import random

histo = ROOT.TH1F("histo", "histo", 100, 0., 100.)

class Kind:
  DQM_PROP_TYPE_MASK     = 0x000000ff
  DQM_PROP_TYPE_SCALAR   = 0x0000000f
  DQM_PROP_TYPE_INVALID  = 0x00000000
  DQM_PROP_TYPE_INT      = 0x00000001
  DQM_PROP_TYPE_REAL     = 0x00000002
  DQM_PROP_TYPE_STRING   = 0x00000003
  DQM_PROP_TYPE_TH1F     = 0x00000010
  DQM_PROP_TYPE_TH1S     = 0x00000011
  DQM_PROP_TYPE_TH1D     = 0x00000012
  DQM_PROP_TYPE_TH2F     = 0x00000020
  DQM_PROP_TYPE_TH2S     = 0x00000021
  DQM_PROP_TYPE_TH2D     = 0x00000022
  DQM_PROP_TYPE_TH3F     = 0x00000030
  DQM_PROP_TYPE_TH3S     = 0x00000031
  DQM_PROP_TYPE_TH3D     = 0x00000032
  DQM_PROP_TYPE_TPROF    = 0x00000040
  DQM_PROP_TYPE_TPROF2D  = 0x00000041
  DQM_PROP_TYPE_DATABLOB = 0x00000050
  DQM_PROP_REPORT_MASK   = 0x00000f00;
  DQM_PROP_REPORT_CLEAR  = 0x00000000;
  DQM_PROP_REPORT_ERROR  = 0x00000100;
  DQM_PROP_REPORT_WARN   = 0x00000200;
  DQM_PROP_REPORT_OTHER  = 0x00000400;
  DQM_PROP_REPORT_ALARM  = (DQM_PROP_REPORT_ERROR
                            | DQM_PROP_REPORT_WARN
                            | DQM_PROP_REPORT_OTHER);

  DQM_PROP_HAS_REFERENCE = 0x00001000;
  DQM_PROP_TAGGED = 0x00002000;
  DQM_PROP_ACCUMULATE = 0x00004000;
  DQM_PROP_RESET = 0x00008000;

  DQM_PROP_NEW = 0x00010000;
  DQM_PROP_RECEIVED = 0x00020000;
  DQM_PROP_LUMI = 0x00040000;
  DQM_PROP_DEAD = 0x00080000;
  DQM_PROP_STALE = 0x00100000;
  DQM_PROP_EFFICIENCY_PLOT = 0x00200000;
  DQM_PROP_MARKTODELETE    = 0x01000000;

class MessageType:

  DQM_MSG_HELLO        = 0;
  DQM_MSG_UPDATE_ME    = 1;
  DQM_MSG_LIST_OBJECTS = 2;
  DQM_MSG_GET_OBJECT   = 3;

  DQM_REPLY_LIST_BEGIN = 101;
  DQM_REPLY_LIST_END   = 102;
  DQM_REPLY_NONE       = 103;
  DQM_REPLY_OBJECT     = 104;

class Message:
  def __init__(self, type):
    self.type_ = type
    self.content_ = bio()
    
  def prepare(self, format, value):
    self.content_.write(struct.pack(format, value))

  def finalize(self):
    # As ugly as it could be....
    length = 36 + sum(struct.unpack('3I', self.content_.getvalue()[24:36]))
    self.content_.seek(0)
    self.content_.write(struct.pack('I', length))

  def getContent(self):
    return self.content_.getvalue()

  def getMessageSize(self):
    return self.content_.tell()

class Message_DQM_REPLY_LIST_BEGIN(Message):
  def __init__(self):
    Message.__init__(self, MessageType.DQM_REPLY_LIST_BEGIN)
    self.content_.write(struct.pack('I', 16))
    self.content_.write(struct.pack('I', self.type_))

  def dump(self):
    print struct.unpack('4I', self.content_.getvalue())

class Message_DQM_REPLY_LIST_END(Message):
  def __init__(self):
    Message.__init__(self, MessageType.DQM_REPLY_LIST_END)
    self.content_.write(struct.pack('I', 16))
    self.content_.write(struct.pack('I', self.type_))

  def dump(self):
    print struct.unpack('4I', self.content_.getvalue())

class Message_DQM_REPLY_OBJECT(Message):
  def __init__(self):
    Message.__init__(self, MessageType.DQM_REPLY_OBJECT)
    self.content_.write(struct.pack('I', 0))
    self.content_.write(struct.pack('I', self.type_))

  def dump(self):
    print struct.unpack('9I', self.content_.getvalue()[0:36])

class Action:
  NONE = 0
  R    = 1
  W    = 2
  A    = 4
  X    = 8
  RW   = R | W

class Request:
  def __init__(self, fd, socket, action, callback, *args, **kwargs):
    self.fd_       = fd
    self.socket_   = socket
    self.action_   = action
    self.callback_ = callback
    self.args_     = args
    self.kwargs_   = kwargs
    self.incoming_ = ''
    self.outgoing_ = ''

  def __str__(self):
    return "fd: %d\naction: %d" % (self.fd_,
                                   self.action_)

class IOEvent:
  def __init__(self, source, event, incoming, outgoing):
    self.source_ = source
    self.event_ = event
    self.incoming_ = incoming
    self.outgoing_ = outgoing

  def __str__(self):
    return "IOEvent of type %s" % self.event_
    
class IOBaseMethod:
  requests = {}

  def __init__(self):
    pass

  def attach(self, request):
    assert ( not (request.socket_.fileno() in self.requests.keys()))
    self.requests[request.socket_.fileno()] = request

  def detach(self, socket):
    assert (socket.fileno() in self.requests.keys())
    self.requests.pop(socket.fileno())

  def request(self, fd):
    assert(fd in self.requests.keys())
    return self.requests[fd]

class IOSelect(IOBaseMethod):
  def __init__(self):
    IOBaseMethod.__init__(self)
    self.rlist_ = []
    self.wlist_ = []
    self.xlist_ = []
    self.ready_all_ = []
    
  def attach(self, request):
    print request
    if request.action_ & (Action.R | Action.A):
      if request.socket_.fileno() not in self.rlist_:
        self.rlist_.append(request.socket_.fileno())

    if request.action_&Action.W:
      if request.socket_.fileno() not in self.wlist_:
        self.wlist_.append(request.socket_.fileno())

    if request.action_&Action.X:
      if request.socket_.fileno() not in self.xlist_:
        self.xlist_.append(request.socket_.fileno())

    IOBaseMethod.attach(self, request)
        
  def detach(self, socket):
    if socket.fileno() in self.rlist_:
      self.rlist_.remove(socket.fileno())
    if socket.fileno() in self.wlist_:
      self.wlist_.remove(socket.fileno())
    if socket.fileno() in self.xlist_:
      self.xlist_.remove(socket.fileno())

    IOBaseMethod.detach(self, socket)

  def wait(self, timeout):
    del self.ready_all_[:]
    assert (timeout >= 0)
    (r, w, x) = select.select(self.rlist_, self.wlist_, self.xlist_, timeout)
    self.ready_all_.extend(map(lambda i: (i, Action.R), r))
    self.ready_all_.extend(map(lambda i: (i, Action.W), w))
    self.ready_all_.extend(map(lambda i: (i, Action.X), x))
    return len(self.ready_all_)

  def next(self):
    for item in self.ready_all_:
      r = self.request(item[0])
      r.action_ = item[1]
      yield r

class IOWatcher:
  def __init__(self):
    self.IOMethod_ = IOSelect()

  def attach(self, socket, action, callback, *args, **kwargs):
    r = Request(socket.fileno(), socket, action, callback, *args, **kwargs)
    self.IOMethod_.attach(r)

  def wait_(self, delay):
    return self.IOMethod_.wait(delay)

  def detach(self, socket):
    self.IOMethod_.detach(socket)

  def dispatch(self, delay):
    assert (delay >= 0)
    if (len(self.IOMethod_.requests) == 0 or not self.wait_(delay)):
      return False

    for r in self.IOMethod_.next():
      ret_value = True
      ev = IOEvent(r.socket_, r.action_, r.incoming_, r.outgoing_)
      if len(r.kwargs_) > 0:
        if len(r.args_) > 0:
          (ret_value, ev_) = r.callback_(ev, r.args_, r.kwargs_)
        else:
          (ret_value, ev_) = r.callback_(ev, r.kwargs_)
      elif len(r.args_) > 0:
        (ret_value, ev_) = r.callback_(ev, r.args_)
      else:
        (ret_value, ev_) = r.callback_(ev)
      # Update request w/ the current status of the event, e.g., for really processed data
      r.incoming_ = ev_.incoming_
      r.outgoing_ = ev_.outgoing_
      if ret_value:
        print "Bye %s/%s" % (ev.source_.getpeername(),
                             ev.source_.getsockname())
        self.detach(ev.source_)
      return True

def readOneMore(msg, format, consumed, length):
  val = struct.unpack(format, msg[consumed:consumed + length])[0]
  consumed = consumed + length
  return (consumed, val)

def onPeerData(ev, args):
  if ev.event_ & Action.R:
    ev.incoming_ = ev.incoming_ + ev.source_.recv(8*1024*1024)
    consumed = 0
    while consumed < len(ev.incoming_):
      print "Consumed: %d, actual: %d, ToBeConsumed: %d" % (consumed,
                                                            len(ev.incoming_),
                                                            len(ev.incoming_[consumed:]))
      if len(ev.incoming_[consumed:]) < 4:
        break
      (consumed, msg_length) = readOneMore(ev.incoming_, 'I', consumed, 4)
      print "received a message of total length: %d " % msg_length
      if  msg_length - 4 > len(ev.incoming_[consumed:]):
        consumed = consumed - 4
        break
      (consumed, msg_type) = readOneMore(ev.incoming_, 'I', consumed, 4)  
      print "received a message of type: %d " % msg_type
      if msg_type == MessageType.DQM_REPLY_LIST_BEGIN:
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        print "Receiving %d objects" % val
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        print "with flag all: %d" % val      
      if msg_type == MessageType.DQM_REPLY_LIST_END:
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        print "EndList Received, updates: %d" % val
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
      if msg_type == MessageType.DQM_REPLY_OBJECT:
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        print "with flags all: %d" % val      
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        (consumed, val) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        print "with tag: %d" % val      
        (consumed, namelen) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        (consumed, datalen) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        (consumed, qlen) = readOneMore(ev.incoming_, 'I', consumed, 4)  
        print "namelen: %d, datalen: %d, qlen: %d" % (namelen, datalen, qlen)
        if namelen:
          (consumed, name) = readOneMore(ev.incoming_, '%ds' % namelen, consumed, namelen)
          print "Retrieved name: %s" % name
        if datalen:
          (consumed, data) = readOneMore(ev.incoming_, '%ds' % datalen, consumed, datalen)
          print "Retrieved data."
        if qlen:
          (consumed, q) = readOneMore(ev.incoming_, '%ds' % qlen, consumed, qlen)
          print "Retrieved qlen,"
    print 'Slicing down internal buffer of %d' % consumed
    ev.incoming_ = ev.incoming_[consumed:]
  return (consumed==0, ev)
  
def decodeMessage(ev, args):
    size = ev.source_.recv(8*1024*1024)
    if len(size) == 0:
        return True
    print len(size)
    return False
#     if len(size) == 0:
#         return True
#     else:
#         type = struct.unpack('I', size)[0]
#         if type == MessageType.DQM_FILL1D:
#             val = struct.unpack('f', ev.source_.recv(4))[0]
#             histo.Fill(val)
#         if type == MessageType.DQM_DUMP:
#             print histo.GetEntries()
#         if type == MessageType.DQM_WRITE:
#             size = struct.unpack('I', ev.source_.recv(4))[0]
#             print size
#             filename = struct.unpack('%ds' % size, ev.source_.recv(size))[0]
#             print filename
#             f = ROOT.TFile(filename, "RECREATE")
#             histo.Write()
#             f.Close()
#             histo.Reset()
#             f.Close()
#
#     return False

def onPeerConnect(ev, args):
  (peer, address) = ev.source_.accept()
  print "Hello %s/%s" % (peer.getpeername(),
                         peer.getsockname())
  peer.setblocking(False)
  args[0].attach(peer, Action.R, onPeerData, args[0])
  return (False, ev)

def onPeerConnectWrite(ev, args):
  (peer, address) = ev.source_.accept()
  print "Hello %s/%s" % (peer.getpeername(),
                         peer.getsockname())
  peer.setblocking(False)
  args[0].attach(c, Action.W, sendMessage, iowatch)
  return (False, ev)

def sendMessage(ev, args):
  print 'SendMessage has been called'
  folder = 'Il/Mio/Folder/Privato'
  me_name = 'A_Fake_Histogram'
  me_content = 'La cacca non sempre profuma %f' % random()
  m = Message_DQM_REPLY_LIST_BEGIN()
  m.prepare('I', 1)
  m.prepare('I', 1)
  m.dump()
  ev.source_.sendall(m.getContent())
  m = Message_DQM_REPLY_OBJECT()
  m.prepare('I', ~Kind.DQM_PROP_DEAD & Kind.DQM_PROP_TYPE_STRING)
  m.prepare('I', 1)
  m.prepare('I', 0)
  m.prepare('I', 0)
  m.prepare('I', len(folder) + len(me_name) + 1) # namelength
  m.prepare('I', len(me_content)) # datalength
  m.prepare('I', 0) # qtlength
  m.prepare('%ds' % (len(folder) + len(me_name) + 1), folder + '/' + me_name)
  m.prepare('%ds' % len(me_content), me_content)
  m.finalize()
  m.dump()
  ev.source_.sendall(m.getContent())
  m = Message_DQM_REPLY_LIST_END()
  m.prepare('I', 1)
  m.prepare('I', 1)
  m.dump()
  ev.source_.sendall(m.getContent())
  sleep(args[0])
  return (False, ev)


def startLocalServer(host, port):
  c = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
  c.bind((host, port)) # bind ANY 
  c.setblocking(False)
  c.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024);
  c.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8*1024*1024);
  c.listen(5)
  iowatch = IOWatcher()
  iowatch.attach(c, Action.A, onPeerConnect, iowatch)
  while 1:
    iowatch.dispatch(10)

def fakeSource(host, port):
  iowatch = IOWatcher()
  c = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
  c.setblocking(1)
  c.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024);
  c.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8*1024*1024);
  c.connect((host, port))
  iowatch.attach(c, Action.W, sendMessage, 10)
  while 1:
    iowatch.dispatch(10)
    
if __name__ == '__main__':
#  startLocalServer('localhost4', 8062)
  fakeSource('localhost4', 8061)
