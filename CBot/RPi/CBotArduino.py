import time
#import smbus

class ArduinoUno :
      i2c = None

      # Arduino Address
      address = 0x04
  
      # Commands
      CMD_TOGGLE_LED = 0x1
      CMD_READ_TEMP = 0x2
      CMD_READ_SONAR1 = 0x3
      CMD_READ_SONAR2 = 0x4
      CMD_READ_IR_LEFT = 0x5
      CMD_READ_IR_RIGHT = 0x6

      # Constructor
      def __init__(self, i2cBus):
#            self.i2c = smbus.SMBus(1); # Force I2C1 (512MB Pi's)
            self.i2c = i2cBus
      
      def toggleLED(self):
          try:
              self.i2c.write_byte(self.address, self.CMD_TOGGLE_LED)
              time.sleep(0.010)
              value = self.i2c.read_byte(self.address)
              #print "TOGGLE_LED: Received: " + str(value)
          except Exception as err:
              print str(err)
          return value

      def getTemp(self):
          value = 0
          try:
              self.i2c.write_byte(self.address, self.CMD_READ_TEMP)
              # Wait 10 ms
              time.sleep(0.010)
              value = self.i2c.read_byte(self.address)
              #print "READ_TEMP: Received: " + str(value)
          except Exception as err:
              print str(err)
          return value

      def getSonar1(self):
          value = 0
          try:
              self.i2c.write_byte(self.address, self.CMD_READ_SONAR1)
              # Wait 10 ms
              #time.sleep(0.010)
              value = self.i2c.read_byte(self.address)
              #print "READ_SONAR1: Received: " + str(value)
          except Exception as err:
              print str(err)
          return value

      def getSonar2(self):
          value = 0
          try:
              self.i2c.write_byte(self.address, self.CMD_READ_SONAR2)
              value = self.i2c.read_byte(self.address)
              #print "READ_SONAR2: Received: " + str(value)
          except Exception as err:
              print str(err)
          return value

      def getIR(self, dir):
          value = 0
          irArray = self.CMD_READ_IR_LEFT
          if (dir == 'R'):
                irArray = self.CMD_READ_IR_RIGHT
          try:
              self.i2c.write_byte(self.address, irArray)
              value = self.i2c.read_byte(self.address)
          except Exception as err:
              print str(err)
          return value




"""
#!/usr/bin/python

import time
from Adafruit_HMC6352 import HMC6352

hmc = HMC6352();

for x in range(0, 300):
    heading = hmc.readData()
    print "Heading: %.1f" % heading
    time.sleep(0.2)



"""



"""
au1 = ArduinoUno()



while True:
#for x in range (1,20):
      au1.toggleLED()
#      au1.readTemp()
      au1.readSonar1()
      au1.readSonar2()
      print "\n"
      time.sleep(1)
      
"""
