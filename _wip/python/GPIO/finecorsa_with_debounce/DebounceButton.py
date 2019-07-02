import RPi.GPIO as GPIO
import time

class DebounceButton:
	# init method needs GPIO channels and debounce time (milliseconds) parameters
	def __init__(self, channel, debounceDelay):
		self.channel = channel
		self.debounceDelay = debounceDelay / 1000.0
		self.lastDebounceTime = 0
		self.status = GPIO.HIGH
		self.lastStatus = GPIO.HIGH
		self.reading = None
		GPIO.setup( self.channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
		
	def update(self):
		self.reading = GPIO.input( self.channel )
		#print( self.reading )
		if self.reading != self.lastStatus:
			#print( "reading diverso da last status")
			self.lastDebounceTime = time.time()
			
		if (time.time() - self.lastDebounceTime) > self.debounceDelay :
			#print( "debounce time strascorso")
			# whatever the reading is at, it's been there for longer than the debounce
			# delay, so take it as the actual current state:
			if self.reading != self.status:
				self.status = self.reading
				#print( "Channel {} status: {}".format(self.channel, self.status) )
		
		self.lastStatus = self.reading
		
	def getStatus(self):
		return self.status
