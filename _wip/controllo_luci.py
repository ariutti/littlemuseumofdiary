#!/usr/bin/env python3

import socket, time

ADDR = "192.168.2.100"
PORT = 4010

def sendUDP(value):
  sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
  sock.sendto(value, (ADDR, PORT))
  
if __name__ == "__main__":
  print("spengo")
  
  sendUDP(b'0') # closed
  """
  time.sleep( 5 )
  sendUDP(b'2') # motion
  time.sleep( 5 )
  sendUDP(b'1') # open
  time.sleep( 5 )
  time.sleep( 5 )
  """
