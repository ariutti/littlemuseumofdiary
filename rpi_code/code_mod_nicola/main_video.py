import sys
import time
import re
import shlex
import argparse
import socket
import pygame
import subprocess as sp
from omxplayer.player import OMXPlayer
import RPi.GPIO as GPIO

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("name", help="name of the diary")
parser.add_argument("address", help="ip address of server")
parser.add_argument("port", help="port of server", type=int)
args = parser.parse_args()

VIDEO_NAME = args.name + ".mp4"
AUDIO_NAME = args.name + ".wav"
IMAGE_NAME = args.name + ".jpg"

IMAGE_WIDTH = 1600
IMAGE_HEIGHT = 900

VIDEO_CURR_REXP = re.compile(r'V :\s*([\d.]+).*')
VIDEO_TOTAL_REXP = re.compile(r'Length : *([\d.]+)*')

ADDR = args.address
PORT = args.port

GPIO_SENSORS = [5, 6, 13]
GPIO_LANG = 19
GPIO_PIN = 21

VIDEO_STARTED = False
VIDEO_PAUSED = False

kill_audio_command = 'sudo pkill -9 -f aplay'
play_audio_command = 'aplay ' + AUDIO_NAME

omx_stdin = None
omx_process = None
tot_sec = None
# print splash screen
def print_intro(name):
  print("""        __...--~~~~~-._   _.-~~~~~--...__
      //               `V'               \\\ 
     //                 |                 \\\ 
    //__...--~~~~~~-._  |  _.-~~~~~~--...__\\\ 
   //__.....----~~~~._\ | /_.~~~~----.....__\\\ 
  ====================\\\|//====================
                      `---`""")
  print("\t[[[[ Diario: " + name.upper() + " ]]]]\n")
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
		# ~ print("Hey! A new input device has been plugged")
		return True
	else:
		# ~ print( "input devices are now equals or less than before" )
		# ~ print( str(inputLen) + " " + str(prevInputLen) )
		prevInputLen = inputLen
		return False
    
inputLen = getInputDevices()
prevInputLen = inputLen

# send data to server over UDP protocol
def sendUDP(value):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  #print('sendUDP ', value)
  sock.sendto(value, (ADDR, PORT))

def setup_buttons():
  GPIO.setmode(GPIO.BCM)
  [GPIO.setup(x, GPIO.IN) for x in GPIO_SENSORS]
  GPIO.setup(GPIO_PIN,GPIO.IN, pull_up_down=GPIO.PUD_UP)
  # setting language gpio
  # ~ GPIO.setup(GPIO_LANG, GPIO.IN)

def read_buttons(): # get index of button pressed
  button = [x for x in GPIO_SENSORS if not(GPIO.input(x))]
  return 0 if not button else GPIO_SENSORS.index(button[0])+1

# get all chapters of video file  
def get_chapters():
	buff = sp.check_output(["ffmpeg", "-i", VIDEO_NAME, "-f",'ffmetadata', "file.txt", '-y'], stderr=sp.STDOUT, universal_newlines=True)
	print(buff)
	chapters = []
	chapters_info = {}
	names = []  
	i = 0
	for line in iter(buff.splitlines()):
		m = re.match(r".*Chapter #(\d+:\d+): start (\d+\.\d+), end (\d+\.\d+).*", line)
		if m != None and m.group(1) not in names:
			names.append(m.group(1))
			chapters.append({ "name": i + 1, "start": float(m.group(2)), "end": float(m.group(3))})
			i = i + 1
	if len(chapters) == 2:
		chapters[len(chapters) - 1]['name'] = 3
	return chapters
# info about video
info_video = {}
chapters = get_chapters()
curr_chapter = 0

# switch language
def switch_language():
  global AUDIO_NAME 
  global play_audio_command
  if AUDIO_NAME.find('_eng') == -1:
    AUDIO_NAME = AUDIO_NAME.replace('.wav', '_eng.wav')
  else:
    AUDIO_NAME = AUDIO_NAME.replace('_eng', '')
  if player:
    play_audio_command = 'aplay ' + AUDIO_NAME
    player.set_position(0)
    k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
    k.wait()
    sp.Popen('aplay ' + AUDIO_NAME, stdout=sp.PIPE, shell=True)

# chapter manager
def handle_chapter(c):
  global curr_chapter
  global run_audio
  curr_chapter = pos2chapter(player.position())
  print('from', curr_chapter, 'to', c)
  # ~ if c != curr_chapter and c in [f['name'] for f in chapters]:
  if c in [f['name'] for f in chapters]:
    cpt = chapters[[y for y, x in enumerate(chapters) if x['name'] == c][0]]
    time.sleep(1)
    print('going to', cpt['start'])
    player.set_position(cpt['start'])
    time.sleep(1)
    k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
    k.wait()
    if c == 1:
      print('playing now')
      # ~ run_audio = aplay(AUDIO_NAME, _bg=True)
      sp.Popen(play_audio_command, stdout=sp.PIPE, shell=True)
    curr_chapter = c
    
    
# check where i am: 
# 0: before chapter 1
# 1: chapter 1
# 2: chapter 2
# 3: chapter 3
# 10 last chapter
def pos2chapter(pos):
  # ~ print('actual position', pos)
  for x in chapters:
    if pos >= x['start'] / 1000 and pos <= x['end']:
      return x['name']
  if pos < chapters[0]['start']:
    return 0
  if pos > chapters[len(chapters) - 1]['end']:
    return chapters[len(chapters) - 1]['name']

# omxplayer player
player = None

print_intro(args.name)

setup_buttons()

pygame.init()
pygame.mouse.set_visible(False)

# init rendering screen
displaymode = (IMAGE_WIDTH , IMAGE_HEIGHT)
screen = pygame.display.set_mode(displaymode)

# load cover image
cover = pygame.image.load(IMAGE_NAME).convert()

# set cover position
position = pygame.Rect((0, 0, IMAGE_WIDTH, IMAGE_HEIGHT))
screen.blit(cover, position)

pygame.display.update()

while True:  
  try:
    if areThereNewInputsDevices():
      sp.Popen('sudo pkill -9 -f python3 && sudo pkill -9 -f omxplayer', stdout=sp.PIPE, shell=True)
    if VIDEO_STARTED == False:
      if (not(GPIO.input(GPIO_PIN))):
        print("Starting video...")
        sendUDP(b'1') # open
        VIDEO_STARTED = True
        VIDEO_PAUSED = False
        time.sleep(.5)
        if player:
          player.quit()
          player = None
        player = OMXPlayer(VIDEO_NAME, args=['--no-osd'])
        time.sleep(1)
        sp.Popen(play_audio_command, stdout=sp.PIPE, shell=True)
        screen.fill((0,0,0))
        pygame.display.update()

    else:

      # check if chapter button is pressed
      if VIDEO_STARTED == True and player:
        chapter = read_buttons()
        # ~ if not GPIO.input(GPIO_LANG):
          # ~ time.sleep(1)
          # ~ switch_language()
        if chapter > 0:
          if VIDEO_PAUSED == True:
            if player:
              player.play()
              VIDEO_PAUSED = False
            print("--- PLAY ---")
            time.sleep(.3)
          handle_chapter(chapter)
        if player.duration() - player.position() < 2 and not VIDEO_PAUSED:
          VIDEO_PAUSED = True
          player.pause()
          # return to italian language
          AUDIO_NAME = AUDIO_NAME.replace('_eng', '')
          play_audio_command = 'aplay ' + AUDIO_NAME
          print('...pausing video')

      # check if is closed
      if GPIO.input(GPIO_PIN):
        sendUDP(b'0') # closed
        VIDEO_STARTED = False
        # return to italian language
        AUDIO_NAME = AUDIO_NAME.replace('_eng', '')
        play_audio_command = 'aplay ' + AUDIO_NAME
        print("Stopping video...")
        player.quit()
        player = None
  
        k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
        k.wait()

        screen.blit(cover, position)        
        pygame.display.update()

    pygame.time.delay(100)

  except KeyboardInterrupt:

    if VIDEO_STARTED == True:
      k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
      k.wait()
      player.quit()
      player = None

    pygame.quit()
    GPIO.cleanup()
    #time.sleep(1)
    sys.exit()
