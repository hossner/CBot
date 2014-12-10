#!/usr/bin/python

import time
#from Adafruit_I2C import Adafruit_I2C

# ===========================================================================
# HMC6352 Class
# ===========================================================================

class HMC6352 :
      i2c = None

      # HMC6352 Address
      address = 0x42 >> 1
  
      # Commands
      CMD_READ_DATA = 0x41
      CMD_ENTER_USER_CALIBRATION = 0x45
      CMD_EXIT_USER_CALIBRATION = 0x4C

      # Constructor
      def __init__(self, i2cBus):
#            self.i2c = Adafruit_I2C(self.address)
            self.i2c = i2cBus


      def readData(self):
            "Read the heading data by write a 0x41 first"
#            self.i2c.write8(0x0, self.CMD_READ_DATA)
            self.i2c.write_byte_data(self.address, 0x0, self.CMD_READ_DATA)            
            # Wait 6 ms
            time.sleep(0.006)
            # Read 2 bytes
#            value = self.i2c.readU16(0x0)
            value = self.i2c.read_word_data(self.address, 0x0)
            # Reverse the data byte order
#            value = self.i2c.reverseByteOrder(value)
            byteCount = len(hex(value)[2:].replace('L','')[::2])
            val = 0
            for i in range(byteCount):
                  val = (val << 8) | (value & 0xff)
                  value >>= 8
            value = val
            # Convert to 360.0 range from the raw integer value
            value = float('%0.1f'%value)/10

            return value
