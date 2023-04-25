import socket
import sys
import time
import json
import threading

hote = "localhost"
port = 2023

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((hote, port))

class Server(threading.Thread):
  def __init__(self, socket):
    threading.Thread.__init__(self)
    self.socket = socket
  
  def run(self):
    while True:
      response = self.socket.recv(2048)
      print(json.loads(response))

server = Server(socket)
server.start()

while True:
  command = input("")
  obj = {
    "action": "play",
    "column": command
  }
  message = json.dumps(obj)
  socket.send(message.encode())

socket.close()