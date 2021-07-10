# TODO: use this same code to manage the three situation
# * digital drawer
# * original drawer
# * shutter

import pygame, sys, time, re, socket, shlex, math, argparse
import subprocess as sp

# DEBUG MACROS
#TODO: add here the USE VIDEO flag in order not to start the video 
USE_VLC = True
USE_CHAPTERS = True
USE_LANGUAGE = False
USE_NETWORK = True

# a pause for the cover image to stay at full screen 
# after having opend the drawer
COVER_PAUSE = 2

## INTERRUTTORI DIGITALI
# imported only to do the cleanup
import RPi.GPIO as GPIO
# a test callback func
def callbackFunction( index ):
	print( "MAIN: chapter callback, this is the index of the button pressed: {}".format(index) )
	videoPlayer.changeChapter( index+1 )
from DigitalSwitch import DigitalSwitch
chSwitches = []
# buttons input
GPIO_SENSORS = [5, 6, 13]
GPIO_LANG = 19
DEBOUNCE_DLY = 300 #ms
for i,pin in enumerate(GPIO_SENSORS):
	chSwitches.append(DigitalSwitch(i,pin, DEBOUNCE_DLY, callbackFunction))
langSwitch = DigitalSwitch(3,GPIO_LANG, DEBOUNCE_DLY,callbackFunction)

## SENSORE DI DISTANZA
from DistanceSensor import DistanceSensor
# rear sensor
R_SENSOR_ID = 0
# value when near
R_SENSOR_MIN = 15
# value when far
R_SENSOR_MAX = 35
# HYSTERESIS
R_SENSOR_HYS = 5 #cm
# FILTER COEFFICIENT A
R_SENSOR_COEFFA = 0.2
# DIRECTION (True: looking to the wall, False: looking to the people)
R_SENSOR_DIR = True

#define open and close callbacks
def openCallback():
	print("MAIN: open callback")
	# adding a pause here to show the cover for a longer time
	print("MAIN: start cover pause")
	time.sleep(2)
	print("MAIN: end cover pause")
	if not videoPlayer.isPlaying():
		print("MAIN: start audio and video")
		videoPlayer.start()
		sendUDP(b'1') # open
		time.sleep(1)
		audioPlayer.start()

		pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
		screen.fill((0,0,0))
		pygame.display.update()

def closeCallback():
	print("MAIN: close callback")
	sendUDP(b'0') # closed
	
	
# sensor ID, MIN, MAX, HYSTERESIS, FILTER COEFF (A), DIRECTION 
sharp = DistanceSensor(R_SENSOR_ID,R_SENSOR_MIN,R_SENSOR_MAX,R_SENSOR_HYS,R_SENSOR_COEFFA,R_SENSOR_DIR, openCallback, closeCallback)

from AudioPlayer import AudioPlayer
audioPlayer = None

from VideoPlayer import VideoPlayer
videoPlayer = None

# get index of button pressed
def read_buttons():
	#print("read buttons")
	#TODO: riscrivila un po' meglio non si capisce nulla
	#button = [x for x in GPIO_SENSORS if not(GPIO.input(x))]
	#return 0 if not button else GPIO_SENSORS.index(button[0])+1
	
	button = [x.getIndex() for x in chSwitches if not(x.getStatus())]
	#print( button )
	if not button:
		return 0
	else:
		return button[0]+1


##### UTILITY ##########################################

# screen
IMAGE_WIDTH = 1024 # 1080
IMAGE_HEIGHT = 768  # 720

# print splash screen
def print_intro(name):
  print("""
        __...--~~~~~-._   _.-~~~~~--...__
      //               `V'               \\\
     //                 |                 \\\
    //__...--~~~~~~-._  |  _.-~~~~~~--...__\\\
   //__.....----~~~~._\ | /_.~~~~----.....__\\\
  ====================\\\|//====================
                      `---`
""")
  print("\t[[[[ Diario: " + name.upper() + " ]]]]\n")


inputLen = 0
prevInputLen = 0
# functions for maintainance with input devices
def getInputDevices():
	cmd  = 'ls /dev/input'
	args = shlex.split( cmd )
	proc = sp.Popen( args, stdout=sp.PIPE )
	output = proc.communicate()[0]
	return len( output.split() )

def areThereNewInputsDevices():
	global inputLen, prevInputLen
	inputLen = getInputDevices()

	# Quit the script only when you plug a new input device.
	# Do nothing but update the 'prevInputLen' when removing it.
	if( inputLen > prevInputLen ):
		#print("Hey! A new input device has been plugged")
		return True
	else:
		#print( "input devices are now equals or less than before" )
		#print( str(inputLen) + " " + str(prevInputLen) )
		prevInputLen = inputLen
		return False

def sendUDP(value):
	if( USE_NETWORK ):
		print("MAIN: Send UDP {}".format(value))
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.sendto(value, (ADDR, PORT))

def killAll():
	print("MAIN: kill all")
	pygame.quit()
	time.sleep(2)
	if videoPlayer.isPlaying():
		videoPlayer.kill()
	if audioPlayer.isPlaying():
		audioPlayer.kill()
	GPIO.cleanup()
	time.sleep(1)
	quit()

def hardKill():
	print("MAIN: hard kill")
	time.sleep(1)
	sp.Popen('sudo killall aplay', stdout=sp.PIPE, shell=True)
	sp.Popen('sudo killall omxplayer; sudo killall omxplayer.bin', stdout=sp.PIPE, shell=True)
	sp.Popen('sudo pkill -9 -f python3 && sudo pkill -9 -f omxplayer', stdout=sp.PIPE, shell=True)
	# TODO: add an hard kill for audio ??
	# TODO: add hard kill for video VLC ??
	# TODO: maybe call the killAll ??


## MAIN ################################################################
if __name__ == "__main__":

	# parse arguments
	parser = argparse.ArgumentParser()
	parser.add_argument("name", help="name of the diary")
	parser.add_argument("address", help="ip address of server")
	parser.add_argument("port", help="port of server", type=int)
	args = parser.parse_args()

	print_intro(args.name)
	
	# server address
	ADDR = args.address
	PORT = args.port
	
	# media files
	VIDEO_NAME = args.name + ".mp4"
	AUDIO_NAME = args.name + ".wav"
	IMAGE_NAME = args.name + ".jpg"

	# initialize pygame
	pygame.init()
	pygame.mouse.set_visible(False)
	# init rendering screen
	displaymode = (IMAGE_WIDTH, IMAGE_HEIGHT)
	screen = pygame.display.set_mode(displaymode)
	pygame.display.toggle_fullscreen()

	# load cover image
	cover = pygame.image.load(IMAGE_NAME).convert()

	# set cover position
	position = pygame.Rect((0, -IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_HEIGHT))
	screen.blit(cover, position)

	audioPlayer = AudioPlayer(AUDIO_NAME)
	videoPlayer = VideoPlayer(VIDEO_NAME, IMAGE_WIDTH, IMAGE_HEIGHT, USE_VLC, audioPlayer, pygame)

	inputLen = getInputDevices()
	prevInputLen = inputLen

	# MAIN LOOP
	while True:
		pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
		try:
			if areThereNewInputsDevices():
				hardKill()
				killAll()

			# update digital switches
			if USE_CHAPTERS:
				for c in chSwitches:
					c.update()   
			#update language switch
			if USE_LANGUAGE:
				langSwitch.update()
			# update distance sensor
			sharp.update()
			
			videoPlayer.update()
			
			"""
			if videoPlayer.needUpdate():
				# menage language
				if( USE_LANGUAGE ):
					if not langSwitch.getStatus():
						time.sleep(1)
						videoPlayer.switch_language()
				# menage chapters
				if( USE_CHAPTERS ):
					chapter = read_buttons()
					print('chapter', chapter)
					videoPlayer.update( chapter )
				else:
					videoPlayer.update( 0 ) # will it work??
					
					
			"""
			"""
			if sharp.isOpen():
				print("sharp is open")
				
				if not videoPlayer.isPlaying():
					print("MAIN: start audio and video")
					videoPlayer.start()
					sendUDP(b'1') # open
					time.sleep(1)
					audioPlayer.start()

					pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0))
					screen.fill((0,0,0))
					pygame.display.update()
				

			elif sharp.isClosed():
				print("sharp is close")
				sendUDP(b'0') # closed
				
			else:
			"""
			if sharp.isMotion():
				print("MAIN: stop audio and video")
				sendUDP(b'2') # motion
				print("distance cm: {}".format(sharp.getValue()) )
				if videoPlayer.isPlaying():
					videoPlayer.stop()
					audioPlayer.stop()

				else:
					# redraw background
					screen.fill((0,0,0))
					new_value = sharp.getNormalized() * (-IMAGE_HEIGHT)
					cover_position = pygame.Rect(0, new_value, IMAGE_WIDTH, IMAGE_HEIGHT)
					screen.blit(cover, cover_position)
					pygame.display.update()
			
			# TODO: evaluate the line below (is it really useful??)
			pygame.time.delay(20)

		except KeyboardInterrupt:
			killAll()
