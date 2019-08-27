#!/usr/bin/env python3

"""
Another quick experiment in trying to implement and debug the distanceSensod class
Here I'm using the class as an external file
"""

## SENSORE DI DISTANZA
from DistanceSensor import DistanceSensor
import time

# rear sensor
R_SENSOR_ID = 0
# value when near
R_SENSOR_MIN = 15
# value when far
R_SENSOR_MAX = 35
# sensor ID, MIN, MAX, HYSTERESIS, FILTER COEFF (A), DIRECTION (True: looking to the wall, False: looking to the people)
sharp = DistanceSensor(R_SENSOR_ID,R_SENSOR_MIN,R_SENSOR_MAX,5,0.2,False)


if __name__ == "__main__":
	print( "main starting ..." )
	time.sleep(1)
	
	while(1):
		sharp.update()
		#print( "{}\t{}\t{}".format(sharp.getRaw(), sharp.getValue(), sharp.getNormalized()))
		#sharp.printStatus()
		
		time.sleep( 0.005 )
