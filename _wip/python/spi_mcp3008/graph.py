#!/usr/bin/env python3

import spidev, time
import matplotlib.pyplot as plt
import matplotlib.animation as animation

# SPI
bus = 0
device = 1 #chip select pin
PAUSE = 0.005

#filter coefficients
A = 0.3
B = 1.0 - A
filtered = 0
#filter stuff
counter=0
xar = []
yar = []

#linearization
linearDistance = 0.0

#min max stuff
MIN=1023
MAX=0


# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
	if ((adcnum > 7) or (adcnum < 0)):
		return -1
	r = spi.xfer2([1,(8+adcnum)<<4,0])
	adcout = ((r[1]&3) << 8) + r[2]
	return adcout


def filter( raw ):
	global filtered
	filtered = A*raw + B*filtered
	return filtered 


def linearize( raw ):
	global linearDistance
	if( raw > 0):
		#linearDistance = (6787.0/(raw - 3))-4
		linearDistance = (6787.0/(raw*0.66 -3))-4
	return linearDistance


def animate(i): 
	global counter;   
	val = readadc(0)
	xar.append( int(counter) )
	#yar.append( int(val) )
	yar.append( linearize(filter(val)) )
	ax1.clear()
	ax1.plot(xar[-30:],yar[-30:])
	counter = counter+1
	

def findMinMax( value ):
	if value < MIN:
		MIN = value
	if value > MAX:
		MAX = value
	
	
if __name__ == "__main__":
	print( "main starting ..." )
	#time.sleep(1)
		
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
	
	fig = plt.figure()
	ax1 = fig.add_subplot(1,1,1)
		
	ani = animation.FuncAnimation(fig, animate, interval=PAUSE*1000)
	plt.show()
	
	# fork a thread here
	# with this function inside
	#print("{}\t[{}\t,\t{}]".format(filtered, MIN, MAX));
		
