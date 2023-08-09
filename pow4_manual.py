import socket
import os
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
      payload = json.loads(response)
      print(payload)
      if payload["type"] == "END":
        print("Gagné : " + str(payload["win"]))
        os._exit(0)


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