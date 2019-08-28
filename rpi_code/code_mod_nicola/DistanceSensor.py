"""
Una classe per gestire il sensore di distanza Sharp.
Va impostata quale la distanza minima e massima assoluta in centimetri
e va specificato se il sensore ha una direzione Vera o Falsa.
* True:  il sensore punta verso il muro dell'edificio (minore distanza=cassetto chiuso; maggiore distanza=cassetto aperto);
* False: il sensore punta verso lo spettatore, contro la parete in legno (minore distanza=cassetto aperto; maggiore distanza:cassetto chiuso).

La classe implementa un sistema per filtrare il dato in ingresso (filtro passa-basso).

La classe fornisce tre stati in uscita (chiuso, aperto, movimento).
La classe inoltre fa uscire un valore continuo (magari normalizzato?)
che rappresenta la distanza del cassetto dalla parete.

Inoltre la classe si occupa di gestire le isteresi negativa e positiva. E fa un check di validazione prima di cominciare.
"""

import spidev, time

class DistanceSensor:

	# static variables
	FIRSTTIMERUNNING = -1
	CLOSED = 0
	OPENED = 1
	MOTION = 2

	# set MIN, MAX and HYS in centimeters
	def __init__(self, sensorId, minimum=10, maximum=50, hys=3, filter_coeff=0.2, direction=True, openCallback=None, closeCallback=None):
		
		print("Distance Sensor init")

		# open communication with distance sensor
		self.spi = spidev.SpiDev()
		self.spi.open(0,1)
		self.spi.max_speed_hz = 500000
		self.spi.mode = 0
		self.adcchannel = sensorId

		# hysteresis stuff
		self.MIN = minimum
		self.MAX = maximum
		self.HYSTERESIS = hys
		self.DIRECTION = direction
		self.READRAW = False

		self.raw = 0
		self.value = 0

		#filter stuff
		self.filter_coeff_A = filter_coeff
		self.filter_coeff_B = 1.0 - self.filter_coeff_A
		self.filtered = 0.0

		# internal state machine
		self.status = self.FIRSTTIMERUNNING

		# get a reference to two callback functions
		# to be called when the distance sensor is passing
		# from state to state.
		self.openCallback = openCallback
		self.closeCallback = closeCallback
		
		# recap print
		print("adcch: {} MIN: {} MAX: {} HYS: {} DIR: {} fcA: {} fcB: {}".format(self.adcchannel, self.MIN, self.MAX, self.HYSTERESIS, self.DIRECTION, self.filter_coeff_A, self.filter_coeff_B))

		self.validateMinMaxHys()

		self.warmUp()

	def validateMinMaxHys(self):
		if self.MIN >= self.MAX:
			print("DISTANCE SENS: Errore nell'impostazioni di minimo e massimo")

		if self.MIN + self.HYSTERESIS > self.MAX:
			print("DISTANCE SENS: Errore nell'impostazioni dell'isteresi")

	def warmUp(self):
		for i in range(20):
			self.raw = self.readadc(self.adcchannel)
			self.value = self.raw2cm(self.filter(self.raw))
			print("DISTANCE SENS: warming up distance sensor... {}".format(self.value))
			time.sleep(0.0125)
		print("DISTANCE SENS: Finish warm up phase")

	def readadc(self, channel):
		if ((channel > 7) or (channel < 0)):
			return -1
		r = self.spi.xfer2([1,(8+channel)<<4,0])
		adcout = ((r[1]&3) << 8) + r[2]
		#print("readadc: {}".format(adcout))
		return adcout

	def filter(self, val):
		self.filtered = val*self.filter_coeff_A + self.filtered*self.filter_coeff_B
		#print("filter: {}".format(self.filtered))
		return self.filtered

	def raw2cm(self, value):
		if( value > 0):
			# LINEARIZE
			#linearDistance = (6787.0/(raw - 3))-4
			linearDistance = (6787.0/(value*0.66 -3))-4
		else:
			return 0
		return linearDistance

	def update(self):
		
		# read sensor value
		self.raw = self.readadc(self.adcchannel)
		self.value  = self.raw2cm(self.filter(self.raw))
		
		#print("Sensor distance update {}".format(round(self.value,2)))

		if self.DIRECTION:
			#print("direction is true")
			if self.value <= self.MIN and self.status != self.CLOSED:
				self.status = self.CLOSED
				# applica una isteresi sul valore minimo
				# per ovviare a falsi positivi MOTION
				self.MIN = self.MIN + self.HYSTERESIS
				#print status insformation
				self.printStatus()
				# call the callback
				if self.closeCallback != None:
					self.closeCallback()

			elif self.value >= self.MAX and self.status != self.OPENED:
				self.status = self.OPENED
				# applica una isteresi sul valore massimo
				# per ovviare a falsi positivi MOTION
				self.MAX = self.MAX - self.HYSTERESIS
				#print status insformation
				self.printStatus()
				# call the callback
				if self.openCallback != None:
					self.openCallback()

			elif self.value > self.MIN and self.value <self.MAX and self.status != self.MOTION:
				# coming from a closed status
				# we have to change the min hysteresis
				if self.status == self.CLOSED:
					self.MIN = self.MIN - self.HYSTERESIS
				elif self.status ==  self.OPENED:
					self.MAX = self.MAX + self.HYSTERESIS
				# if we are between MIN and MAX at startup
				# do nothing with these values
				elif self.status == self.FIRSTTIMERUNNING:
					print("DISTANCE SENS: startup in the middle of MIN, MAX: doing nothing with hysteresis")
				# however change the status to MOTION
				self.status = self.MOTION
				self.printStatus()

		else:
			if self.value <= self.MIN and self.status != self.OPENED:
				self.status = self.OPENED
				# applica una isteresi sul valore minimo
				# per ovviare a falsi positivi MOTION
				self.MIN = self.MIN + self.HYSTERESIS
				#print status insformation
				self.printStatus()
				# call the callback
				if self.openCallback != None:
					self.openCallback()

			elif self.value >= self.MAX and self.status != self.CLOSED:
				self.status = self.CLOSED
				# applica una isteresi sul valore massimo
				# per ovviare a falsi positivi MOTION
				self.MAX = self.MAX - self.HYSTERESIS
				#print status insformation
				self.printStatus()
				# call the callback
				if self.closeCallback != None:
					self.closeCallback()
					
			elif self.value > self.MIN and self.value <self.MAX and self.status != self.MOTION:
				# coming from a closed status
				# we have to change the min hysteresis
				if self.status == self.CLOSED:
					self.MAX = self.MAX + self.HYSTERESIS
				elif self.status ==  self.OPENED:
					self.MIN = self.MIN - self.HYSTERESIS
				# if we are between MIN and MAX at startup
				# do nothing with these values
				elif self.status == self.FIRSTTIMERUNNING:
					print("DISTANCE SENS: startup in the middle of MIN, MAX: doing nothing with hysteresis")
				# however change the status to MOTION
				self.status = self.MOTION
				self.printStatus()

	def getValue(self):
		return self.value

	def getRaw(self):
		return self.raw

	def getNormalized(self):
		directionValue = None
		if self.DIRECTION:
			normalizedValue = ((self.MAX - self.value)*1.0)/(self.MAX-self.MIN)
		else:
			normalizedValue = ((self.value-self.MIN)*1.0)/(self.MAX-self.MIN)
		return normalizedValue

	def getStatus(self):
		return self.status

	def printStatus(self):
		if self.status == self.OPENED:
			print("DISTANCE SENS: OPENED")
		elif self.status == self.CLOSED:
			print("DISTANCE SENS: CLOSED")
		elif self.status == self.MOTION:
			print("DISTANCE SENS: MOTION")
		else:
			print("other")
		print("DISTANCE SENS: HYS:{} - MIN:{} - MAX:{}".format(self.HYSTERESIS, self.MIN, self.MAX))

	def isOpen(self):
		return self.status == self.OPENED

	def isClosed(self):
		return self.status == self.CLOSED

	def isMotion(self):
		return self.status == self.MOTION
