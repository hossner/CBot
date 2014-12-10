import sys
import threading
import Queue
import smbus
import socket
import struct
import CBotArduino
import CBotHMC6352
import RPi.GPIO as GPIO

# the following will probably be removed...
import time
import random

TIME_WAIT = 60
CBOT_TCP_BUFFER_SIZE = 80

SPEEDS = [0, 70, 90, 100]
SLOWDOWN_TIME = 0.2  # Nr of seconds between switching motor between forward/backward
# ================= PropulsionThread ====================

class PropulsionThread(threading.Thread):
    def __init__(self, Q2main, Q2propulsion):
        threading.Thread.__init__(self)
        self.queue2main = Q2main
        self.myQueue = Q2propulsion
        self.stop = False
        self.tmpBuf = None
        self.state = 0
        self.frequency = 50
        self.motorState = [0, 0] # Left and right respectively
        GPIO.setmode(GPIO.BOARD)

        self.IN3 = 16 #18 #22 #16 #18 #16 #22    #16 # IN3
        self.IN4 = 18 #22 #18 #18 #16 #22 #16    #18 # IN4
        self.EN2 = 22 #16 #16 #22 #22 #18 #18    #22 # EN2

        self.IN1 = 11 #13 #15 #11 #15 #11 #13    #11 # IN1
        self.IN2 = 13 #11 #11 #13 #13 #15 #15    #13 # IN2
        self.EN1 = 15 #15 #13 #15 #11 #13 #11    #15 # EN1

        GPIO.setup(self.IN1,GPIO.OUT)
        GPIO.setup(self.IN2,GPIO.OUT)
        GPIO.setup(self.IN3,GPIO.OUT)
        GPIO.setup(self.IN4,GPIO.OUT)
        GPIO.setup(self.EN1,GPIO.OUT)
        GPIO.setup(self.EN2,GPIO.OUT)

        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        GPIO.output(self.IN4, GPIO.LOW)
        GPIO.output(self.EN1, GPIO.HIGH)
        GPIO.output(self.EN2, GPIO.HIGH)

        """
        self.MotorLF = GPIO.PWM(self.IN1, self.frequency)
        self.MotorLB = GPIO.PWM(self.IN2, self.frequency)
        self.MotorRF = GPIO.PWM(self.IN4, self.frequency)
        self.MotorRB = GPIO.PWM(self.IN3, self.frequency)
        """

    def run(self):
        print self, ' Propulsion thread started'
        while (not self.stop):
            self.tmpBuf = self.myQueue.get()
            self.handleCmd(self.tmpBuf)
        print self, ' Propulsion thread stopping...'
        self.allStop()
        GPIO.cleanup()

    def cmdStop(self):
        self.stop = True
        self.myQueue.put('INT_PRO_STOP')

    def allStop(self):
        # Here, all propulsion should go to stop
        time.sleep(0.2)

    def handleCmd(self, cmd):
        if (cmd == 'INT_PRO_STOP'):
            self.stop = True
        elif (cmd == 'FWD'):
            self.state = self.move('F')
        elif (cmd == 'BACK'):
            self.state = self.move('B')
        elif (cmd == 'HALT'):
            self.state = self.halt()
        elif (cmd == 'LEFT'):
            if (self.state == 0):
                self.state = self.swivel('L')
            elif (self.state == 1):
                self.state = self.turn('FL')
            elif (self.state == 2):
                self.state = self.turn('BL')
            elif (self.state == 3):
                None
            elif (self.state == 4):
                self.state = self.move('F')
            elif (self.state == 5):
                None
            elif (self.state == 6):
                self.state = self.move('B')
            elif (self.state == 7):
                None
            elif (self.state == 8):
                self.state = self.halt()

        elif (cmd == 'RIGHT'):
            if (self.state == 0):
                self.state = self.swivel('R')
            elif (self.state == 1):
                self.state = self.turn('FR')
            elif (self.state == 2):
                self.state = self.turn('BR')
            elif (self.state == 3):
                self.state = self.move('F')
            elif (self.state == 4):
                None
            elif (self.state == 5):
                self.state = self.move('B')
            elif (self.state == 6):
                None
            elif (self.state == 7):
                self.state = self.halt()
            elif (self.state == 8):
                None


    # ==== Low level functions
    def forwardL(self):
        if self.motorState[0] == -1:
            GPIO.output(self.IN2, GPIO.LOW)
            time.sleep(SLOWDOWN_TIME)
        GPIO.output(self.IN1, GPIO.HIGH)
        self.motorState[0] = 1

    def forwardR(self):
        if self.motorState[1] == -1:
            GPIO.output(self.IN3, GPIO.LOW)
            time.sleep(SLOWDOWN_TIME)
        GPIO.output(self.IN4, GPIO.HIGH)
        self.motorState[1] = 1

    def backwardL(self):
        if self.motorState[0] == 1:
            GPIO.output(self.IN1, GPIO.LOW)
            time.sleep(SLOWDOWN_TIME)
        GPIO.output(self.IN2, GPIO.HIGH)
        self.motorState[0] = -1

    def backwardR(self):
        if self.motorState[1] == 1:
            GPIO.output(self.IN4, GPIO.LOW)
            time.sleep(SLOWDOWN_TIME)
        GPIO.output(self.IN3, GPIO.HIGH)
        self.motorState[1] = -1

    def haltL(self):
        GPIO.output(self.IN1, GPIO.LOW)
        GPIO.output(self.IN2, GPIO.LOW)
        self.motorState[0] = 0

    def haltR(self):
        GPIO.output(self.IN4, GPIO.LOW)
        GPIO.output(self.IN3, GPIO.LOW)
        self.motorState[1] = 0

    # ========== Middle level functions =======

    def move(self, direction):
        if (direction == 'F'):
            self.forwardL()
            self.forwardR()
            return 1
        elif (direction == 'B'):
            self.backwardL()
            self.backwardR()
            return 2
        return -1

    def turn(self, direction):
        if (direction == 'FL'):
            self.haltL()
            self.forwardR()
            return 3
        elif (direction == 'FR'):
            self.haltR()
            self.forwardL()
            return 4
        elif (direction == 'BL'):
            self.haltL()
            self.backwardR()
            return 5
        elif (direction == 'BR'):
            self.haltR()
            self.backwardL()
            return 6
        return -1

    def swivel(self, direction):
        if (direction == 'L'):
            self.backwardL()
            self.forwardR()
            return 7
        elif (direction == 'R'):
            self.forwardL()
            self.backwardR()
            return 8
        return -1

    def halt(self):
        self.haltL()
        self.haltR()
        return 0

# ================= ReceiverThread ====================

class ReceiverThread(threading.Thread):
    def __init__(self, Q2main, Q2receiver, CBotIP, CBotTCPPort):
        threading.Thread.__init__(self)
        self.queue2main = Q2main
        self.myQueue = Q2receiver
        self.tmpBuf = ''
        self.stop = False
        self.bufLen = None
        self.conn = None
        self.cbotSocket = 0
        self.cbotIP = CBotIP
        self.cbotPort = CBotTCPPort
        self.connected = False

    def run(self):
        print self, ' Receiver thread started'
        print '  Listening on TCP '+self.cbotIP+':'+str(self.cbotPort)
        self.cbotSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        hadToWait = 0
        while (not self.connected) and (not self.stop):
            try:
                if hadToWait >= TIME_WAIT:
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    print " ...giving up!"
                    self.stop = True
                    self.queue2main.put('CMD_STOP')
                    break
                self.cbotSocket.bind((self.cbotIP, self.cbotPort))
                if (hadToWait > 0) :
                    sys.stdout.write('\n')
                    sys.stdout.flush()
                    print " ...OK, got it!"
                self.connected = True
            except:
                sys.stdout.write(" Receiver thread trying to bind to port %s on local IP %s...%3d (%s)\r" % (self.cbotPort, self.cbotIP, hadToWait, TIME_WAIT))
                sys.stdout.flush()
                hadToWait = hadToWait + 1
                time.sleep(1)
        while (not self.stop):
            self.cbotSocket.listen(1)
            try:
                self.conn, self.addr = self.cbotSocket.accept()
            except:
                break
            try:
                self.conn.settimeout(1.0)
                self.tmpBuf = self.conn.recv(CBOT_TCP_BUFFER_SIZE)
                print 'Here: '+ self.tmpBuf
            except:
                None
            if self.tmpBuf:
                self.conn.send('ACK_'+self.tmpBuf) # Echo received command back as confirmation
                self.queue2main.put(self.tmpBuf)

        print self, '  Receiver thread stopping...'


    def cmdStop(self):
        self.stop = True
        try:
            self.cbotSocket.shutdown(socket.SHUT_RDWR)
            self.cbotSocket.close()
        except:
            None
        if self.conn:
            self.conn.shutdown(socket.SHUT_RDWR)
            self.conn.close()

# ================= SenderThread ====================
class SenderThread(threading.Thread):
    def __init__(self, Q2main, Q2sender, ServerIP, ServerUDPPort):
        threading.Thread.__init__(self)
        self.queue2main = Q2main
        self.myQueue = Q2sender
        self.tmpBuf = ''
        self.stop = False
        self.bufLen = 0
        self.serverIP = ServerIP
        self.serverPort = ServerUDPPort
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def run(self):
        print self, 'Sender thread started'
        print '   Sending to server at '+self.serverIP+':'+str(self.serverPort)
        try:
            self.runChecks()
        except:
            raise BaseException

        while (not self.stop):
            try:
                self.tmpBuf = self.myQueue.get(True, 1)
            except:
                None
            else:
                self.socket.sendto(self.tmpBuf, (self.serverIP, self.serverPort))

        print self, ' Sender thread stopping...'

    def cmdStop(self):
        self.stop = True

    def runChecks(self):
        time.sleep(1)


# ================= TelemetryThread ====================

class TelemetryThread(threading.Thread):
    def __init__(self, Q2main, Q2telemetry, Q2sender):
        threading.Thread.__init__(self)
        self.queue2main = Q2main
        self.myQueue = Q2telemetry
        self.queue2sender = Q2sender
        self.i2cBus = None
        self.arduino1 = None
        self.compass = None
        self.stop = False

    def run(self):
        print self, 'Telemetry thread started'
        try:
            self.i2cBus = smbus.SMBus(1) # Force I2C1 (512MB Pi's)
            self.arduino1 = CBotArduino.ArduinoUno(self.i2cBus)
            self.compass = CBotHMC6352.HMC6352(self.i2cBus)
        except Exception as err:
            print str(err)
            raise BaseException

        while (not self.stop):
            self.probeSensors()

        print self, '  Telemetry thread stopping...'


    def cmdStop(self):
        self.stop = True

    def probeSensors(self):
        val = self.compass.readData()
        self.queue2sender.put('0:'+str(val))
        val = self.arduino1.getTemp()
        self.queue2sender.put('1:'+str(val))
        val = self.arduino1.getSonar1()
        self.queue2sender.put('2:'+str(val))
        val = self.arduino1.getSonar2()
        self.queue2sender.put('3:'+str(val))
        val = self.arduino1.getIR('L')
        self.queue2sender.put('4:'+str(val))
#        val = self.arduino1.getIR('R')
#        self.queue2sender.put('5:'+str(val))
        time.sleep(0.01)
