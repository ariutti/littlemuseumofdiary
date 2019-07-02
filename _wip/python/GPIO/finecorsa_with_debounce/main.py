#!/usr/bin/env python3

import RPi.GPIO as GPIO
from DebounceButton import DebounceButton
import time

FINECORSA_PIN = 21
PAUSE = 0.01



if __name__ == "__main__":
	GPIO.setmode(GPIO.BCM)
	finecorsa = DebounceButton(FINECORSA_PIN, 59)
	
	try:
		while(1):
			#read the input
			finecorsa.update()
			value = finecorsa.getStatus()
			print( value )
			time.sleep(PAUSE)
			
	except:
		print("cleanup")
		GPIO.cleanup()
