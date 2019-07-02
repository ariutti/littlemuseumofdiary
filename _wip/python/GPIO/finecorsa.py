#!/usr/bin/env python3

import RPi.GPIO as GPIO
import time

FINECORSA = 21

GPIO.setmode(GPIO.BCM)

GPIO.setup( FINECORSA, GPIO.IN, pull_up_down=GPIO.PUD_UP )


try:
	while(1):
		#read the input
		value = GPIO.input(FINECORSA) 
		print( value )
		time.sleep(0.25)
		
except:
	print("cleanup")
	GPIO.cleanup()
