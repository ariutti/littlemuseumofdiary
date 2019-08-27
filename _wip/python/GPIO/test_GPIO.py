#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

myPins = [5,6,13] # and 19
PAUSE = 0.0125

GPIO.setmode(GPIO.BCM)

for pin in myPins:
	GPIO.setup( pin, GPIO.IN )


try:
	while(1):
		#read the input
		values = [GPIO.input(pin) for pin in myPins]
		"""
		for v in values:
			if v == 0:
				print( "falso positivo")
		"""
		print( values )
		time.sleep(PAUSE)
		"""
		for pin in myPins:
			value = GPIO.input( myPin )
			print( value )
			time.sleep(0.25)
		"""
except:
	print("cleanup")
	GPIO.cleanup()
	
