#!/usr/bin/env python3

"""
An initial test trying to debug the DistanceSensor class.
Here I put a semplified class directly inside the main file.
It seems to work
"""

import spidev, time
PAUSE = 0.125

class SHARP:
	
	def __init__(self):
		self.A = 0.3
		self.B = 1.0 - self.A
		self.filtered = 0.0
		
		self.bus = 0
		self.device = 1 #chip select pin
		
		# open communication with distance sensor
		print( "initialize SPI device" )
		self.spi = spidev.SpiDev()
		# bus 0 and device 0 (chip select pin)
		self.spi.open(self.bus,self.device)
		self.spi.max_speed_hz = 500000
		self.spi.mode = 0
	
	def getDistance(self, raw ):
		if( raw > 0):
			#linearDistance = (6787.0/(raw - 3))-4
			linearDistance = (6787.0/(raw*0.66 -3))-4
		return linearDistance

	def getVoltage(self, raw ):
		return raw * (3.3 / 1024)

	def filter(self, raw):
		value = raw*self.A + self.filtered*self.B
		self.filtered = value
		return self.filtered
		
	# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
	def readadc(self, adcnum):
		if ((adcnum > 7) or (adcnum < 0)):
			return -1
		r = self.spi.xfer2([1,(8+adcnum)<<4,0])
		adcout = ((r[1]&3) << 8) + r[2]
		#val = (int)(4800/(adcout - 20)) #sharp linearization
		#return val
		return adcout
		

sharp = SHARP()

if __name__ == "__main__":
	print( "main starting ..." )
	time.sleep(1)
	
	while(1):
		val = sharp.readadc(0)
		#print( "{}".format(val))
		print( "{}\t{}\t{}".format(val, round(sharp.getVoltage(val),2), round(sharp.getDistance( sharp.filter(val) ) )))
		
		time.sleep( PAUSE )
		

