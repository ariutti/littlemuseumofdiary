#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

myPins = [5,13,6]

GPIO.setmode(GPIO.BCM)

for pin in myPins:
	GPIO.setup( pin, GPIO.IN )


try:
	while(1):
		#read the input
		values = [GPIO.input(pin) for pin in myPins]
		print( values )
		time.sleep(0.25)
		"""
		for pin in myPins:
			value = GPIO.input( myPin )
			print( value )
			time.sleep(0.25)
		"""
except:
	print("cleanup")
	GPIO.cleanup()
	
	
	
