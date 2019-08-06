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
	def __init__(self, sensorId, min=10, max=50, his=3, filter_coeff=0.2, dir=True, openCallback={}, closeCallback={}):

		# open communication with distance sensor
		self.spi = spidev.SpiDev()
		self.spi.open(0,1)
		self.spi.max_speed_hz = 500000
		self.spi.mode = 0
		self.adcchannel = sensorId

		# hysteresis stuff
		self.MIN = min
		self.MAX = max
		self.HISTERESIS = his
		self.DIRECTION = dir
		self.READRAW = False

		self.raw =None
		self.value = None

		#filter stuff
		self.filter_coeff_A = filter_coeff
		self.filter_coeff_B = 1.0 - self.filter_coeff_A
		self.filtered = None

		# internal state machine
		self.status = self.FIRSTTIMERUNNING

		# get a reference to two callback functions
		# to be called when the distance sensor is passing
		# from state to state.
		self.openCallback = openCallback
		self.closeCallback = closeCallback

		self.validateMinMaxHys()

		self.warmUp()

	def validateMinMaxHys():
		if self.MIN >= self.MAX:
			print("Errore nell'impostazioni di minimo e massimo")

		if self.MIN + self.HYSTERESIS > self.MAX:
			print("Errore nell'impostazioni dell'isteresi")

	def warmUp(self):
		for i in range(20):
			self.raw = readadc(self.adcchannel)
			self.value = getCm(filter(self.raw))
			print("warming up distance sensor... {}".format(self.value))
			time.sleep(0.0125)
		print("Finish warm up phase")

	def readadc(self, adcchannel):
		if ((adcchannel > 7) or (adcchannel < 0)):
			return -1
		r = spi.xfer2([1,(8+adcchannel)<<4,0])
		adcout = ((r[1]&3) << 8) + r[2]
		return adcout

	def filter(self, input):
		value = input*self.filter_coeff_A + self.filtered*self.filter_coeff_B
		self.filtered = value
		return self.filtered

	def raw2cm(self, input):
		if( input > 0):
			# LINEARIZE
			#linearDistance = (6787.0/(raw - 3))-4
			linearDistance = (6787.0/(raw*0.66 -3))-4
		else:
			return 0
		return linearDistance

	def update(self):
		# read sensor value
		self.raw = readadc(R_SENSOR_ID)
		self.value  = raw2cm(filter(self.raw))

		if self.DIRECTION:
			if self.value <= self.MIN and self.status != self.CLOSED:
				self.status = self.CLOSED
				# applica una isteresi sul valore minimo
				# per ovviare a falsi positivi MOTION
				self.MIN = self.MIN + self.HYSTERSIS
				# call the callback
				self.closeCallback()
			elif self.value >= self.MAX and self.status != self.OPEN:
				self.status = self.OPENED
				# applica una isteresi sul valore massimo
				# per ovviare a falsi positivi MOTION
				self.MAX = self.MAX - self.HYSTERESIS
				# call the callback
				self.openCallback()
			elif self.status != self.MOTION:
				# coming from a closed status
				# we have to change the min hysteresis
				if self.status == self.CLOSED:
					self.MIN = self.MIN - self.HYSTERESIS
				elif self.status ==  self.OPENED:
					self.MAX = self.MAX + self.HYSTERESIS
				# if we are between MIN and MAX at startup
				# do nothing with these values
				elif self.status == self.FIRSTTIMERUNNING:
					print("startup in the middle of MIN, MAX: doing nothing with hysteresis")
				# however change the status to MOTION
				self.status = self.MOTION

		else:
			if self.value <= self.MIN and self.status != self.OPENED:
				self.status = self.OPENED
				# applica una isteresi sul valore minimo
				# per ovviare a falsi positivi MOTION
				self.MIN = self.MIN + self.HYSTERSIS
				# call the callback
				self.openCallback()
			elif self.value >= self.MAX and self.status != self.CLOSED:
				self.status = self.CLOSED
				# applica una isteresi sul valore massimo
				# per ovviare a falsi positivi MOTION
				self.MAX = self.MAX - self.HYSTERESIS
				# call the callback
				self.closeCallback()
			elif self.status != self.MOTION:
				# coming from a closed status
				# we have to change the min hysteresis
				if self.status == self.CLOSED:
					self.MAX = self.MAX + self.HYSTERESIS
				elif self.status ==  self.OPENED:
					self.MIN = self.MIN - self.HYSTERESIS
				# if we are between MIN and MAX at startup
				# do nothing with these values
				elif self.status == self.FIRSTTIMERUNNING:
					print("startup in the middle of MIN, MAX: doing nothing with hysteresis")
				# however change the status to MOTION
				self.status = self.MOTION

	def getValue(self):
		return self.getValue

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

	def isOpen(self):
		return self.status == self.OPENED

	def isClosed(self):
		return self.status == self.CLOSED

	def isMotion(self):
		return self.status == self.MOTION
