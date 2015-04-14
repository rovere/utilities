from collector import *
import random
import datetime

NUMFILL = 100000

def sendMessage(ev):
    m = Message(MessageType.DQM_FILL1D)
    before = datetime.datetime.utcnow()
    for i in range(0, NUMFILL):
        m.prepare(3.141516, append=True)
#        m.prepare(random.gauss(50,10), append=True)
    after = datetime.datetime.utcnow()
    print "%d ROOT fills in " % NUMFILL, after-before
    print "Sending a message of size: %d for %d entries" % (m.getMessageSize(),
                                                            NUMFILL)
    ev.source_.sendall(m.getContent())
    return False

if __name__ == '__main__':
    iowatch = IOWatcher()
    c = socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0)
    c.setblocking(1)
    c.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 8*1024*1024);
    c.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 8*1024*1024);
    c.connect(('128.141.38.171', 9091))
    iowatch.attach(c, Action.W, sendMessage)
    counter = 0
    before = datetime.datetime.utcnow()
    while counter < 1:
        if not iowatch.dispatch(0.0000001):
            break
        counter += 1
    after = datetime.datetime.utcnow()
    m = Message(MessageType.DQM_DUMP)
    m.prepare()
    c.sendall(m.getContent())
    m = Message(MessageType.DQM_WRITE)
    m.prepare("finalFile.root")
    c.sendall(m.getContent())
    c.close()
    print "%d fills in " % NUMFILL, after-before
