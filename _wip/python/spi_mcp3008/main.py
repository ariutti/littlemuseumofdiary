#!/usr/bin/env python3

import spidev, time

bus = 0
device = 1 #chip select pin
PAUSE = 0.125

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
	if ((adcnum > 7) or (adcnum < 0)):
		return -1
	r = spi.xfer2([1,(8+adcnum)<<4,0])
	adcout = ((r[1]&3) << 8) + r[2]
	#val = (int)(4800/(adcout - 20)) #sharp linearization
	#return val
	return adcout
  
 
 
if __name__ == "__main__":
	print( "main starting ..." )
	time.sleep(1)
	
	# open communication with distance sensor
	print( "initialize SPI device" )
	spi = spidev.SpiDev()
	# bus 0 and device 0 (chip select pin)
	spi.open(bus,device)
	#time.sleep(1)	
	#spi.no_cs = True
	#spi.cshigh = True
	#spi.max_speed_hz = 5000
	#spi.mode = 0b01
	#spi.mode = 0b11
	spi.max_speed_hz = 500000
	spi.mode = 0
	
	while(1):
		val = readadc(0)
		print( val )
		time.sleep( PAUSE )
		
