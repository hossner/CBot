import threading
import socket
import time
import wx
import Queue
import CBotServerGUI



# --------------------- Receiver Thread -------------------------

class ReceiverThread(threading.Thread):
    def __init__(self, serverConfig, mainQueue, receiverQueue, aiQueue):
        threading.Thread.__init__(self)
        self.serverConfig = serverConfig
        self.mainQueue = mainQueue
        self.myQueue = receiverQueue
        self.aiQueue = aiQueue

        self.stop = False
        self.receiving = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        print self, "  Receiver thread started"
        print '  Will listen on ' + self.serverConfig.serverIP + ':' + str(self.serverConfig.udpPort) + ' (UDP)'
        try:
            self.sock.bind((self.serverConfig.serverIP, self.serverConfig.udpPort))
        except socket.error, e:
            print e[1]
            raise BaseException

        while (not self.stop):
            data, addr = self.sock.recvfrom(self.serverConfig.bufferSize)
            tlf = data.split(':', 1)
            # 0 = compass
            # 1 = temperature
            # 2 = rear sonar
            # 3 = front sonar
            # 4 = IR array left
            # 5 = IR array right
            #if (tlf[0] == '4'):
            #    print "  Receiver thread got: " + data
            cmd = data.split('_', 1)
            if isinstance(cmd[0], int):
                self.aiQueue.put(data)
            else:
                self.mainQueue.put(data)
        print self, '  Receiver thread stopping'


    def cmdStop(self):
        self.stop = True
        try:
            self.sock.shutdown(socket.SHUT_RDWR)
            self.sock.close()
        except:
            None

# --------------------- Sender Thread -------------------------

class SenderThread(threading.Thread):
    def __init__(self, serverConfig, mainQ, senderQ):
        threading.Thread.__init__(self)
        self.serverConfig = serverConfig
        self.mainQ = mainQ
        self.myQueue = senderQ

        self.stop = False
        self.isConnected = False
        self.sock = None
        self.tmpBuf = None

    def run(self):
        print self, "  Sender thread starting"
        print self, self.myQueue
        print '  Will send to ' + self.serverConfig.cbotIP + ':' + str(self.serverConfig.tcpPort) + ' (TCP)'
        while (not self.stop):
            try:
                self.tmpBuf = self.myQueue.get()
            except:
                self._setSenderStatus('')
            else:
                if (self.tmpBuf == 'INT_SND_STOP'):
                    break
                try:
                    self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.sock.connect((self.serverConfig.cbotIP, self.serverConfig.tcpPort))
                    self.sock.send(self.tmpBuf)
                    data = self.sock.recv(self.serverConfig.bufferSize)
                    # TBA: Check that data equals sent command...
                except:
                    self._setSenderStatus('Connection refused...')

        print self, '  Sender thread stopping'
        try:
            self.sock.shutdown(sock.SHUT_RDWR)
            self.sock.close()
        except:
            None

    def _setSenderStatus(self, statusTxt):
        print statusTxt
        None

    def cmdStop(self):
        self.stop = True
        self.myQueue.put('INT_SND_STOP')

# --------------------- AI Thread -------------------------

class AIThread(threading.Thread):
    def __init__(self, serverCfg, mainQueue, aiQueue, senderQueue):
        threading.Thread.__init__(self)
        self.serverCfg = serverCfg
        self.mainQueue = mainQueue
        self.myQueue = aiQueue
        self.senderQueue = senderQueue
        self.stop = False
        self.tmpBuf = ''

    def run(self):
        print self, "  AI thread started"
        while (not self.stop):
            self.tmpBuf = self.myQueue.get()
            self.handleCmd(self.tmpBuf)
        print self, "  AI thread stopping"

    def cmdStop(self):
        self.myQueue.put('STOP')
        self.stop = True

    def handleCmd(self, cmd):
        print "Handling: " + cmd
        if (cmd == 'STOP'):
            self.stop = True
