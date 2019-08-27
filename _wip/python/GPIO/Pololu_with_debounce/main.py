#!/usr/bin/env python3

import time
import RPi.GPIO as GPIO

## INTERRUTTORI DIGITALI
from DigitalSwitch import DigitalSwitch
chSwitches = []
# buttons input
GPIO_SENSORS = [5, 6, 13]
GPIO_LANG = 19
DEBOUNCE_DLY = 100 #ms

def callbackFunction( index ):
	print( "this is the index of the button pressed: {}".format(index) )

for index, pin in enumerate(GPIO_SENSORS):
	chSwitches.append(DigitalSwitch(index, pin, DEBOUNCE_DLY, callbackFunction))

"""
# get index of button pressed
def read_buttons():
	#TODO: riscrivila un po' meglio non si capisce nulla
	button = [x for x in GPIO_SENSORS if not(GPIO.input(x))]
	return 0 if not button else GPIO_SENSORS.index(button[0])+1
"""


try:
	while(1):
		for c in chSwitches:
			c.update()
	#print([c.getStatus() for c in chSwitches])
	time.sleep(0.005)
except:
	print("cleanup")
	GPIO.cleanup()

