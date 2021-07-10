import pygame
import sys
import spidev
import time
import re
import argparse
import socket
import subprocess as sp
import shlex
import math
from omxplayer.player import OMXPlayer
import vlc
import mouse
import RPi.GPIO as GPIO

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("name", help="name of the diary")
parser.add_argument("address", help="ip address of server")
parser.add_argument("port", help="port of server", type=int)
args = parser.parse_args()

# media files
VIDEO_NAME = args.name + ".mp4"
AUDIO_NAME = args.name + ".wav"
IMAGE_NAME = args.name + ".jpg"

# server address
ADDR = args.address
PORT = args.port

# screen
IMAGE_WIDTH = 1024
IMAGE_HEIGHT = 768

# buttons input
GPIO_SENSORS = [5, 6, 13]
GPIO_LANG = 19 

# rear sensor
R_SENSOR_ID = 0
# value when near
#R_SENSOR_MIN = 700
R_SENSOR_MIN = 15
# value when far
#R_SENSOR_MAX = 300
R_SENSOR_MAX = 30
DISTANCE_HYSTERESIS = 3

VIDEO_STARTED = False
VIDEO_PAUSED = False

# number of samples for filtering
NUM_CAMP = 5

omx_stdin = None
omx_process = None
tot_sec = None

# audio process
run_audio = None
kill_audio_command = 'sudo pkill -9 -f aplay'
play_audio_command = 'aplay ' + AUDIO_NAME

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

def sendUDP(value):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(value, (ADDR, PORT))

def setup_buttons():
  GPIO.setmode(GPIO.BCM)
  [GPIO.setup(x, GPIO.IN) for x in GPIO_SENSORS]
  # setting language gpio
  # ~ GPIO.setup(GPIO_LANG, GPIO.IN)

def read_buttons(): # get index of button pressed
  button = [x for x in GPIO_SENSORS if not(GPIO.input(x))]
  return 0 if not button else GPIO_SENSORS.index(button[0])+1

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
  if ((adcnum > 7) or (adcnum < 0)):
    return -1
  r = spi.xfer2([1,(8+adcnum)<<4,0])
  adcout = ((r[1]&3) << 8) + r[2]
  return adcout
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
# vlc handle_chapter
def handle_chapter_vlc(c):
  global vlcPlayer
  global VIDEO_PAUSED
  print('going to', len(chapters), c)
  if len(chapters) == 2:
    if c == 3:  
      print(1)
      vlcPlayer.set_chapter(1)
    if c == 1:
      print(2)
      vlcPlayer.set_chapter(0)
  else:
    vlcPlayer.set_chapter(c - 1)
  if VIDEO_PAUSED == True:
    # ~ if player:
    time.sleep(0.5)
    vlcPlayer.set_pause(0)
    VIDEO_PAUSED = False
    print('is playing ', vlcPlayer.is_playing())
  k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
  k.wait()
  if c == 1:
    sp.Popen(play_audio_command, stdout=sp.PIPE, shell=True)
    
    
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
print('info video', chapters)
A = 0.2
B = 1.0 - A
filtered = 0
def filter(raw):
  global filtered
  value = raw*A + filtered*B
  filtered = value
  return filtered

def getDistance( raw ):
  # ~ global linearDistance
  if( raw > 0):
    #linearDistance = (6787.0/(raw - 3))-4
    linearDistance = (6787.0/(raw*0.66 -3))-4
  else:
    return 0
  return linearDistance

def kill_all():
  pygame.quit()
  time.sleep(2)
  if VIDEO_STARTED == True:
    # ~ player.quit()
    # ~ player = None
    vlcPlayer.stop()
  if run_audio:
    a = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
    a.wait()
  GPIO.cleanup()
  #time.sleep(1)
  quit()
  
print_intro(args.name)

# open communication with distance sensor
spi = spidev.SpiDev()
spi.open(0,1)
spi.max_speed_hz = 500000
spi.mode = 0

setup_buttons()

pygame.init()
# init rendering screen
displaymode = (IMAGE_WIDTH , IMAGE_HEIGHT)
screen = pygame.display.set_mode(displaymode)
pygame.display.toggle_fullscreen()
# load cover image
cover = pygame.image.load(IMAGE_NAME).convert()

# set cover position
position = pygame.Rect((0, -IMAGE_HEIGHT, IMAGE_WIDTH, IMAGE_HEIGHT))
screen.blit(cover, position)

#vlc media player
vlcInstance = vlc.Instance()
media = vlcInstance.media_new('/home/pi/code/' + VIDEO_NAME)

# Create new instance of vlc player
vlcPlayer = vlcInstance.media_player_new()
vlcPlayer.stop()

# Pass pygame window id to vlc player, so it can render its contents there.
win_id = pygame.display.get_wm_info()['window']
vlcPlayer.set_xwindow(win_id)
vlcPlayer.set_media(media)
i = 0
r_acc = 0
mouse.move(IMAGE_WIDTH, IMAGE_HEIGHT, True, 0)

# WARM Up the distance sensor
for i in range(20):
  r_val = readadc(R_SENSOR_ID)
  r_sensor_value = getDistance(filter(r_val))
  print("warming up distance sensor... {}".format(r_sensor_value))
  time.sleep(0.0125)
print("Finish warm up phase")


while True:
  pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0)) 
  try:
    if areThereNewInputsDevices():
      sp.Popen('sudo pkill -9 -f python3 && sudo pkill -9 -f aplay', stdout=sp.PIPE, shell=True)
    # read rear sensor value
    r_val = readadc(R_SENSOR_ID)
    r_sensor_value = getDistance(filter(r_val))

    if True:
    # ~ if i == NUM_CAMP:

      if VIDEO_STARTED == True:
        """
        #TMP vediamo se il problema del video che riparte da solo
        # è dovuto agli interruttori digitali
        
        chapter = read_buttons()
        # ~ if not GPIO.input(GPIO_LANG):
          # ~ time.sleep(1)
          # ~ switch_language()
        # ~ print('chapter', chapter)
        if chapter != 0:
          handle_chapter_vlc(chapter)
        if  vlcPlayer.get_length() - vlcPlayer.get_time() < 2000 and not VIDEO_PAUSED:
          VIDEO_PAUSED = True
          vlcPlayer.set_pause(1)
          # return to italian language
          AUDIO_NAME = AUDIO_NAME.replace('_eng', '')
          play_audio_command = 'aplay ' + AUDIO_NAME
          print('...pausing video')
        """

      i = 0
      r_acc = 0

      #print('R: ', r_sensor_value)

      if r_sensor_value <= R_SENSOR_MIN:

        if VIDEO_STARTED == False:
          print("Starting video...")
          sendUDP(b'1') # open
          VIDEO_STARTED = True
          VIDEO_PAUSED = False
          vlcPlayer.play()
          time.sleep(1)
          sp.Popen(play_audio_command, stdout=sp.PIPE, shell=True)
          pygame.mouse.set_cursor((8,8),(0,0),(0,0,0,0,0,0,0,0),(0,0,0,0,0,0,0,0)) 
          screen.fill((0,0,0))
          pygame.display.update()
          R_SENSOR_MIN = R_SENSOR_MIN + DISTANCE_HYSTERESIS
      
      elif r_sensor_value >= R_SENSOR_MAX:
        sendUDP(b'0') # closed

      else:
        sendUDP(b'2') # motion

        if VIDEO_STARTED == True:
          VIDEO_STARTED = False
          R_SENSOR_MIN = R_SENSOR_MIN - DISTANCE_HYSTERESIS
          vlcPlayer.stop()
          # ~ player = None
          k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
          k.wait()
          print("Stopping video...")

        else:
          # redraw background
          screen.fill((0,0,0))
          #new_value = ((R_SENSOR_MAX - r_sensor_value) * (-IMAGE_HEIGHT))/(R_SENSOR_MAX-R_SENSOR_MIN)
          new_value = ((r_sensor_value - R_SENSOR_MIN) * (-IMAGE_HEIGHT))/(R_SENSOR_MAX-R_SENSOR_MIN)
          cover_position = pygame.Rect(0, new_value, IMAGE_WIDTH, IMAGE_HEIGHT)
          screen.blit(cover, cover_position)
          pygame.display.update()

    else:
      i += 1
      r_acc += r_sensor_value
    # ~ print(r_sensor_value)
    pygame.time.delay(int(100/NUM_CAMP))
  except KeyboardInterrupt:
    kill_all()
