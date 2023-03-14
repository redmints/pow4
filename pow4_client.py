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
  command = command.split(" ")
  if len(command) > 0:
    if command[0] == "get_last_inserted":
      obj = {
        "action": command[0],
        "column": command[1]
      }
    if command[0] == "get_board":
      obj = {
        "action": command[0]
      }
    if command[0] == "play":
      obj = {
        "action": command[0],
        "column": command[1]
      }
    message = json.dumps(obj)
    socket.send(message.encode())

socket.close()