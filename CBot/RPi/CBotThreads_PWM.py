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

# ================= PropulsionThread ====================

class PropulsionThread(threading.Thread):
    def __init__(self, Q2main, Q2propulsion):
        threading.Thread.__init__(self)
        self.queue2main = Q2main
        self.myQueue = Q2propulsion
        self.stop = False
        self.tmpBuf = None
        self.motorState = [0, 0]
        self.state = 0
        self.frequency = 50
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

        self.MotorLF = GPIO.PWM(self.IN1, self.frequency)
        self.MotorLB = GPIO.PWM(self.IN2, self.frequency)
        self.MotorRF = GPIO.PWM(self.IN4, self.frequency)
        self.MotorRB = GPIO.PWM(self.IN3, self.frequency)

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
            self.state = self.move('F', 3)
        elif (cmd == 'BACK'):
            self.state = self.move('B', 3)
        elif (cmd == 'HALT'):
            self.state = self.halt()
        elif (cmd == 'LEFT'):
            if (self.state == 0):
                print "Swiveling Left"
                self.swivel('L', 3)
            else:
                self.state = self.turn('L', 2, 3)
        elif (cmd == 'RIGHT'):
            if (self.state == 0):
                print "Swiveling Right"
                self.swivel('R', 3)
            else:
                self.state = self.turn('R', 3, 2)

    # ==== Low level functions
    def moveL(self, speed):
        if ((speed < -3) or (speed > 3)):
            return -1
        if (self.motorState[0] == speed):
            return 0
        if (speed == 0):
            self.MotorLF.stop()
            self.MotorLB.stop()
        elif (self.motorState[0] == 0):
            if (speed > 0):
                self.MotorLF.start(SPEEDS[speed])
            else:
                self.MotorLB.start(SPEEDS[-speed])
        elif (self.motorState[0] > 0):
            if (speed > 0):
                self.MotorLF.ChangeDutyCycle(SPEEDS[speed])
            else:
                self.MotorLF.stop()
                self.MotorLB.start(SPEEDS[-speed])
        elif (self.motorState[0] < 0):
            if (speed < 0):
                self.MotorLB.ChangeDutyCycle(SPEEDS[-speed])
            else:
                self.MotorLB.stop()
                self.MotorLF.start(SPEEDS[speed])
        self.motorState[0] = speed
        return 0

    def moveR(self, speed):
        if ((speed < -3) or (speed > 3)):
            return -1
        if (self.motorState[1] == speed):
            return 0
        if (speed == 0):
            self.MotorRB.stop()
            self.MotorRF.stop()
        elif (self.motorState[1] == 0):
            if (speed > 0):
                self.MotorRF.start(SPEEDS[speed])
            else:
                self.MotorRB.start(SPEEDS[-speed])
        elif (self.motorState[1] > 0):
            if (speed > 0):
                self.MotorRF.ChangeDutyCycle(SPEEDS[speed])
            else:
                self.MotorRF.stop()
                self.MotorRB.start(SPEEDS[-speed])
        elif (self.motorState[1] < 0):
            if (speed < 0):
                self.MotorRB.ChangeDutyCycle(SPEEDS[-speed])
            else:
                self.MotorRB.stop()
                self.MotorRF.start(SPEEDS[speed])
        self.motorState[1] = speed
        return 0

    def halt(self):
        self.MotorLF.stop()
        self.MotorLB.stop()
        self.MotorRF.stop()
        self.MotorRB.stop()
        self.motorState = [0, 0]

    # ========== Middle level functions =======

    def move(self, direction, speed):
        if (speed < -3) or (speed > 3):
            return -1
        state = 0
        if (speed == 0):
            state = 0
        elif (direction == 'F'):
            state = 1
        elif (direction == 'B'):
            state = 2
            speed = -speed
        self.moveL(SPEEDS[speed])
        self.moveR(SPEEDS[speed])
        return state

    def turn(self, direction, speedL, speedR):
        state = 0
        if (speedL < -3) or (speedL > 3) or (speedR < -3) or (speedR > 3):
            return -1

        self.forwardL(SPEEDS[speedL])
        self.forwardR(SPEEDS[speedR])
        state = 1
        return state

    def swivel(self, direction, speed):
        state = 0
        if (speed >= 0) and (speed <= 3):
            if (direction == 'L'):
                state = 6
                self.backwardL(SPEEDS[speed])
                self.forwardR(SPEEDS[speed])
        elif (direction == 'R'):
            state = 7
            self.forwardL(SPEEDS[speed])
            self.backwardR(SPEEDS[speed])
        return state
            

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
        #self.cbotSocket.settimeout(1.0)

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
