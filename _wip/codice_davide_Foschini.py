import sys
import time
import shlex
import spidev
import argparse
import socket
import subprocess as sp
import RPi.GPIO as GPIO

# parse arguments
parser = argparse.ArgumentParser()
parser.add_argument("name", help="name of the diary")
parser.add_argument("address", help="ip address of server")
parser.add_argument("port", help="port of server", type=int)
args = parser.parse_args()

AUDIO_NAME = args.name + ".wav"

ADDR = args.address
PORT = args.port

# rear sensor
R_SENSOR_ID = 0
# value when near
R_SENSOR_MIN = 35 #cm
# value when far
R_SENSOR_MAX = 50 #cm
HYSTERESIS = 10

GPIO_LANG = 19 
# setting language gpio
GPIO.setmode(GPIO.BCM)
# ~ GPIO.setup(GPIO_LANG, GPIO.IN)
AUDIO_STARTED = False
# audio commands
kill_audio_command = 'sudo pkill -9 -f aplay'
play_audio_command = 'aplay ' + AUDIO_NAME

NUM_CAMP = 5

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

# read SPI data from MCP3008 chip, 8 possible adc's (0 thru 7)
def readadc(adcnum):
  if ((adcnum > 7) or (adcnum < 0)):
    return -1
  r = spi.xfer2([1,(8+adcnum)<<4,0])
  adcout = ((r[1]&3) << 8) + r[2]
  return adcout
# sensor coefficients 
A = 0.3
B = 1.0 - A
filtered = 0
# filter signal
def filter(raw):
  global filtered
  value = raw*A + filtered*B
  filtered = value
  return filtered
  
# get distance from raw signal
def getDistance( raw ):
  # ~ global linearDistance
  if( raw > 0):
    #linearDistance = (6787.0/(raw - 3))-4
    linearDistance = (6787.0/(raw*0.66 -3))-4
  else:
    return 0
  return linearDistance
  
def sendUDP(value):
  print("Send UDP {}".format(value))
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(value, (ADDR, PORT))

# switch language
def switch_language():
  global AUDIO_NAME 
  global AUDIO_NAME
  if AUDIO_NAME.find('_eng') == -1:
    AUDIO_NAME = AUDIO_NAME.replace('.wav', '_eng.wav')
  else:
    AUDIO_NAME = AUDIO_NAME.replace('_eng', '')
  play_audio_command = 'aplay ' + AUDIO_NAME
  k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
  k.wait()
  sp.Popen('aplay ' + AUDIO_NAME, stdout=sp.PIPE, shell=True)

# open communication with distance sensor
spi = spidev.SpiDev()
spi.open(0,1)
spi.max_speed_hz = 500000
spi.mode = 0

i = 0
r_acc = 0

# WARM Up the distance sensor
for i in range(20):
  print("warming up distance sensor...")
  r_val = readadc(R_SENSOR_ID)
  r_sensor_value = getDistance(filter(r_val))
  

while True:  
  try:
    if areThereNewInputsDevices():
      sp.Popen('sudo pkill -9 -f python3', stdout=sp.PIPE, shell=True)
    # read rear sensor value
    r_val = readadc(R_SENSOR_ID)
    r_sensor_value = getDistance(filter(r_val))
    #print("filtered {}".format(r_sensor_value))

    if True:
    # ~ if i == NUM_CAMP:

      # ~ r_sensor_value = r_acc / NUM_CAMP
      i = 0
      r_acc = 0

      if r_sensor_value >= R_SENSOR_MAX:
        # ~ if not GPIO.input(GPIO_LANG):
          # ~ time.sleep(1)
          # ~ switch_language()
        if AUDIO_STARTED == False:
          print("Starting audio...")
          print("read ", r_sensor_value)
          sendUDP(b'1') # open
          AUDIO_STARTED = True
          sp.Popen(play_audio_command, stdout=sp.PIPE, shell=True)
          R_SENSOR_MAX = R_SENSOR_MAX - HYSTERESIS

      elif r_sensor_value <= R_SENSOR_MIN:
        sendUDP(b'0') # closed

      else:
        sendUDP(b'2') # motion
   
        if AUDIO_STARTED == True:
          AUDIO_STARTED = False
          R_SENSOR_MAX = R_SENSOR_MAX + HYSTERESIS
          print("Stopping audio...")
          print("read ", r_sensor_value)	
          k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
          k.wait()
           # return to italian language
          AUDIO_NAME = AUDIO_NAME.replace('_eng', '')
          play_audio_command = 'aplay ' + AUDIO_NAME

    else:
      i += 1
      r_acc += r_sensor_value


    time.sleep(.05)

  except KeyboardInterrupt:

    if AUDIO_STARTED == True:
      k = sp.Popen(kill_audio_command, stdout=sp.PIPE, shell=True)
      k.wait()
    sys.exit()
