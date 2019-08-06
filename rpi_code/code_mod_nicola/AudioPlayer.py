"""
La classe contiene la gestione per del player audio.
"""

import subprocess as sp

class AudioPlayer:

	KILL_AUDIO_CMD = 'sudo pkill -9 -f aplay'
	PLAY_AUDIO_CMD = 'aplay '

	def __init__(self, AUDIO_NAME):
		self.run_audio = None
		self.AUDIO_FILE = AUDIO_NAME
		self.PLAY_AUDIO_CMD = self.PLAY_AUDIO_CMD + self.AUDIO_FILE
		self.STARTED = False

	def isPlaying(self):
		return self.STARTED

	# return to italian language
	def switchToITA(self):
		print("Audio: back to ITA...")
		self.AUDIO_FILE = self.AUDIO_FILE.replace('_eng', '')
		self.PLAY_AUDIO_CMD = 'aplay ' + self.AUDIO_FILE

	# switch language
	def switch_language(self):
		print("Audio: switch language...")
		if self.AUDIO_NAME.find('_eng') == -1:
			self.AUDIO_FILE = self.AUDIO_FILE.replace('.wav', '_eng.wav')
		else:
			self.AUDIO_FILE = self.AUDIO_FILE.replace('_eng', '')

		self.stop()
		self.PLAY_AUDIO_CMD = 'aplay ' + self.AUDIO_FILE
		self.start()

	def start(self):
		print("Starting audio...")
		self.STARTED = True
		sp.Popen( self.PLAY_AUDIO_CMD, stdout=sp.PIPE, shell=True)

	def stop(self):
		print("Stop audio...")
		self.STARTED = False
		k = sp.Popen( self.KILL_AUDIO_CMD, stdout=sp.PIPE, shell=True)
		k.wait()

	def kill(self):
		print("Kill audio...")
		k = sp.Popen( self.KILL_AUDIO_CMD, stdout=sp.PIPE, shell=True)
		k.wait()
