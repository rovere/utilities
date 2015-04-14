#!/usr/bin/env python

import socket
import select
import struct
import ROOT
from io import BytesIO as bio

histo = ROOT.TH1F("histo", "histo", 100, 0., 100.)

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
        
    def prepare(self, *args, **kwargs):
        if len(kwargs) and 'append' in kwargs.keys() and not kwargs['append']:
            self.content_.truncate(0)
        self.content_.write(struct.pack('I', self.type_))
        if self.type_ == MessageType.DQM_FILL1D:
            assert (len(args) > 0)
            self.content_.write(struct.pack('f', args[0]))
        if self.type_ == MessageType.DQM_WRITE:
            assert(len(args)) > 0
            self.content_.write(struct.pack('I', len(args[0])))
            self.content_.write(struct.pack('%ds' % len(args[0]), args[0]))

    def getContent(self):
        return self.content_.getvalue()

    def getMessageSize(self):
        return self.content_.tell()

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

    def __str__(self):
        return "fd: %d\naction: %d" % (self.fd_,
                                       self.action_)

class IOEvent:
    def __init__(self, source, event):
        self.source_ = source
        self.event_ = event
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
            ev = IOEvent(r.socket_, r.action_)
            if len(r.kwargs_) > 0:
                if len(r.args_) > 0:
                    ret_value = r.callback_(ev, r.args_, r.kwargs_)
                else:
                    ret_value = r.callback_(ev, r.kwargs_)
            elif len(r.args_) > 0:
                    ret_value = r.callback_(ev, r.args_)
            else:
                ret_value = r.callback_(ev)
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
    msg = ev.source_.recv(8*1024*1024)
    consumed = 0
    while consumed < len(msg):
      print "Consumed: %d, actual: %d, ToBeConsumed: %d" % (consumed,
                                                            len(msg),
                                                            len(msg[consumed:]))
      if len(msg[consumed:]) < 4:
        msg = msg + ev.source_.recv(8*1024*1024)
      (consumed, msg_length) = readOneMore(msg, 'I', consumed, 4)
      print "received a message of total length: %d " % msg_length
      if  msg_length - 4 > len(msg[consumed:]):
        msg = msg + ev.source_.recv(8*1024*1024)
      (consumed, msg_type) = readOneMore(msg, 'I', consumed, 4)  
      print "received a message of type: %d " % msg_type
      if msg_type == MessageType.DQM_REPLY_LIST_BEGIN:
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        print "Received %d objects" % val
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        print "with flag all: %d" % val      
      if msg_type == MessageType.DQM_REPLY_LIST_END:
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        print "EndList Received, updates: %d" % val
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
      if msg_type == MessageType.DQM_REPLY_OBJECT:
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        print "with flags all: %d" % val      
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        (consumed, val) = readOneMore(msg, 'I', consumed, 4)  
        print "with tag: %d" % val      
        (consumed, namelen) = readOneMore(msg, 'I', consumed, 4)  
        (consumed, datalen) = readOneMore(msg, 'I', consumed, 4)  
        (consumed, qlen) = readOneMore(msg, 'I', consumed, 4)  
        print "namelen: %d, datalen: %d, qlen: %d" % (namelen, datalen, qlen)
        if namelen:
          (consumed, name) = readOneMore(msg, '%ds' % namelen, consumed, namelen)
          print "Retrieved name: %s" % name
        if datalen:
          (consumed, data) = readOneMore(msg, '%ds' % datalen, consumed, datalen)
          print "Retrieved data."
        if qlen:
          (consumed, q) = readOneMore(msg, '%ds' % qlen, consumed, qlen)
          print "Retrieved qlen,"
  return False
  
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
    return False

if __name__ == '__main__':
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    c.bind(('127.0.0.1', 8062)) # bind ANY 
    c.setblocking(False)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024);
    c.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8*1024*1024);
    c.listen(5)
    iowatch = IOWatcher()
    iowatch.attach(c, Action.A, onPeerConnect, iowatch)
    while 1:
        iowatch.dispatch(10)
        
