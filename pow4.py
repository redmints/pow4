import socket
import threading
import json
import sys
import os
import time
from tkinter import *
from random import *

game = None
clients = []
print_char = {}
print_color = {}
has_one = False

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.bind(('', 2023))
socket.listen(5)

class Client(threading.Thread):
    def __init__(self, ip, port, socket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socket = socket
        print("New client from " + str(self.ip) + " on port " + str(self.port))

    def send(self, payload):
        self.socket.send(payload)

    def getName(self):
        return str(self.ip)+str(self.port)

    def run(self):
        global clients
        global game
        global print_char
        global print_color
        global t

        while True:
            response = self.socket.recv(2048)
            if response == b'':
                break
            if response != "":
                try:
                    payload = json.loads(response)
                except:
                    continue
                if game:
                    if ("action" in payload) and (payload["action"] == "play") and ("column" in payload) and (payload["column"].isdigit()):
                        if game.last == self.getName():
                            obj = {
                                "type": "ERR",
                                "payload": "WAIT_FOR_PLAYER"
                            }
                            self.send(json.dumps(obj).encode())
                            continue
                        x, y = game.put(int(payload["column"]), self.getName())
                        print(str(self.ip)+':'+str(self.port)+" --> x : "+str(x)+" y : "+str(y))
                        if (x != None) and (y != None):
                            t.changeColor(x, y, print_color[self.getName()])
                            finished = game.isFinished(x, y, self.getName())
                            if finished != None:
                                print("Game finished --> " + str(finished) + " WIN !!!")
                                obj = {
                                    "type": "END",
                                    "win": True,
                                }
                                self.send(json.dumps(obj).encode())
                                obj = {
                                    "type": "END",
                                    "win": False,
                                }
                                if game.client1 == self:
                                    game.client2.send(json.dumps(obj).encode())
                                else:
                                    game.client1.send(json.dumps(obj).encode())
                                break
                            obj = {
                                "type": "PLAY_INFO",
                                "play": False,
                                "payload": game.board
                            }
                            self.send(json.dumps(obj).encode())
                            obj = {
                                "type": "PLAY_INFO",
                                "play": True,
                                "payload": game.board
                            }
                            if game.client1 == self:
                                game.client2.send(json.dumps(obj).encode())
                            else:
                                game.client1.send(json.dumps(obj).encode())
                        else:
                            obj = {
                                "type": "ERR",
                                "payload": "BAD_INPUT"
                            }
                            self.send(json.dumps(obj).encode())
                    else:
                        obj = {
                            "type": "ERR",
                            "payload": "BAD_PAYLOAD"
                        }
                        self.send(json.dumps(obj).encode())
                else:
                    obj = {
                        "type": "ERR",
                        "payload": "GAME_NOT_STARTED"
                    }
                    self.send(json.dumps(obj).encode())
        print("Connexion lost with " + str(self.ip) + " on port " + str(self.port))
        clients.remove(self)
        del print_char[self.getName()]
        del print_color[self.getName()]
        if len(clients) < 2:
            print("Game finished !")
            game = None
            has_one = False


class Game():
    def __init__(self, client1, client2):
        self.client1 = client1
        self.client2 = client2
        self.last = None
        self.board = [[0 for x in range(6)] for y in range(7)]
        print("Starting game...")

    def start(self):
        rand = randrange(10000)%2
        objTrue = {
                "type": "START",
                "play": True
            }
        objFalse = {
                "type": "START",
                "play": False
            }
        if rand == 0:
            self.client1.send(json.dumps(objTrue).encode())
            self.client2.send(json.dumps(objFalse).encode())
            self.last = self.client2.getName()
        else:
            self.client2.send(json.dumps(objTrue).encode())
            self.client1.send(json.dumps(objFalse).encode())
            self.last = self.client1.getName()

    def getLastInserted(self, column):
        for i in range(len(self.board[column])):
            if self.board[column][i] == 0:
                return i-1
        return 5

    def put(self, column, client_instance):
        if column >= 0 and column <= 6:
            last_inserted = self.getLastInserted(column)
            if last_inserted < 5 and self.board[column][last_inserted + 1] == 0:
                self.board[column][last_inserted + 1] = client_instance
                self.last = client_instance
                return column, last_inserted + 1
        return None, None

    def isFinished(self, x, y, client):
        axis_x = self.searchOnAxis(x, y, client, 'x')
        if axis_x != None:
            return axis_x
        axis_y = self.searchOnAxis(x, y, client, 'y')
        if axis_y != None:
            return axis_y
        axis_g_d = self.searchOnAxis(x, y, client, 'diag_g_d')
        if axis_g_d != None:
            return axis_g_d
        axis_d_g = self.searchOnAxis(x, y, client, 'diag_d_g')
        if axis_d_g != None:
            return axis_d_g
        return None

    def searchOnAxis(self, x, y, client, axis):
        cpt = 1
        cur = client
        cur_x = x
        cur_y = y
        while cur == client:
            if axis == 'x':
                cur_x -= 1
            if axis == 'y':
                cur_y -= 1
            if axis == 'diag_g_d':
                cur_x -= 1
                cur_y += 1
            if axis == 'diag_d_g':
                cur_x -= 1
                cur_y -= 1
            if cur_x > 6 or cur_x < 0:
                break
            if cur_y > 5 or cur_y < 0:
                break
            cur = self.board[cur_x][cur_y]
            if cur == client:
                cpt += 1
            if cpt == 4:
                return client
        cur = client
        cur_x = x
        cur_y = y
        while cur == client:
            if axis == 'x':
                cur_x += 1
            if axis == 'y':
                cur_y += 1
            if axis == 'diag_g_d':
                cur_x += 1
                cur_y -= 1
            if axis == 'diag_d_g':
                cur_x += 1
                cur_y += 1
            if cur_x > 6 or cur_x < 0:
                break
            if cur_y > 5 or cur_y < 0:
                break
            cur = self.board[cur_x][cur_y]
            if cur == client:
                cpt += 1
            if cpt == 4:
                return client
        return None

    def printBoard(self):
        os.system("clear")
        global print_char
        for line in range(5, -1, -1):
            for column in range(7):
                if self.board[column][line] == 0:
                    sys.stdout.write(str(self.board[column][line]))
                else:
                    sys.stdout.write(print_char[str(self.board[column][line])])
            sys.stdout.write("\n")

class GUI():
    def __init__(self,root):
        self.cells = {}
        for i in range(6):
            for j in range(7):
                cell = Frame(root, bg='white', highlightbackground="black",
                     highlightcolor="black", highlightthickness=1,
                     width=120, height=120, padx=3, pady=3)
                cell.grid(row=i, column=j)
                self.cells[(i, j)] = cell

    def changeColor(self, x, y, color):
        self.cells[(5-y, x)].configure(background=color)

class Server(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        global clients
        global has_one
        global print_char
        global print_color
        global game
        while True:
            (client, (ip, port)) = socket.accept()
            if len(clients) == 2:
                client.close()
                continue
            newthread = Client(ip, port, client)
            clients.append(newthread)
            if not has_one:
                print_char[str(ip)+str(port)] = 'x'
                print_color[str(ip)+str(port)] = "red"
                has_one = True
            else:
                print_char[str(ip)+str(port)] = 'o'
                print_color[str(ip)+str(port)] = "blue"
            newthread.start()
            if (len(clients) == 2 and game == None):
                game = Game(clients[0], clients[1])
                game.start()


root = Tk()
t = GUI(root)

server = Server()
server.start()

root.mainloop()