"""
Sensore digitale per la selezione dei capitoli.
Attualmente identificati nei sensori Sharp con driver Pololu 810.
La classe implementa un sistema per risolvere i noiosi falsi positivisi con un debounce software.

"""
import time
import RPi.GPIO as GPIO

class DigitalSwitch:

	def __init__(self, index, pin, debounceDelay, callbackFunc=None):
		self.index = index
		self.pin = pin
		self.debounceDelay = debounceDelay / 1000.0
		self.lastDebounceTime = 0
		self.status = GPIO.HIGH
		self.lastStatus = GPIO.HIGH
		self.reading = None
		GPIO.setmode(GPIO.BCM)
		# TODO: disable default pullup/pulldown
		GPIO.setup( self.pin, GPIO.IN)
		self.callbackFunc = callbackFunc

	def update(self):
		self.reading = GPIO.input( self.pin )
		#print( self.reading )

		if self.reading != self.lastStatus:
			#print( "reading diverso da last status")
			self.lastDebounceTime = time.time()

		self.lastStatus = self.reading

		if (time.time() - self.lastDebounceTime) > self.debounceDelay :
			#print( "debounce time strascorso")
			# whatever the reading is at, it's been there for longer than the debounce
			# delay, so take it as the actual current state:
			if self.reading != self.status:
				self.status = self.reading
				#print( "index {} channel {} status: {}".format(self.index, self.pin, self.status) )
				# eventually call a callback function here
				if self.status == False :
					# the switch is Pressed
					if self.callbackFunc != None:
						self.callbackFunc( self.index )

					
	def getStatus(self):
		return self.status
