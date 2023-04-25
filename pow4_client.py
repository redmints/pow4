import socket
import sys
import json

hote = "localhost"
port = 2023

socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socket.connect((hote, port))
to_me = False
board = None
me = None
other = None

def send(obj):
   message = json.dumps(obj)
   socket.send(message.encode())

def getLast(x, board):
  y = 0
  res = board[x][0]
  while res != 0:
    y += 1
    if y > 5:
       return 5
    res = board[x][y]
  return y

def getScore(board, id):
  score = 0
  # Pour les lignes
  for y in range(6):
    for x in range(4):
      align = 0
      for jeton in range(4):
        if board[x+jeton][y] == id:
          if jeton == 0:
            if board[x+jeton+1][y] == 0 or board[x+jeton+1][y] == id:
              align += 1
          elif jeton == 3:
            if board[x+jeton-1][y] == 0 or board[x+jeton-1][y] == id:
              align += 1
          else:
            if board[x+jeton-1][y] == 0 or board[x+jeton-1][y] == id or board[x+jeton+1][y] == 0 or board[x+jeton+1][y] == id:
              align += 1
      if align == 4:
        align = 10000
      score += align
  # Pour les colonnes
  for x in range(7):
    for y in range(3):
      align = 0
      for jeton in range(4):
        if board[x][y+jeton] == id:
          if jeton == 0:
            if board[x][y+jeton+1] == 0 or board[x][y+jeton+1] == id:
              align += 1
          elif jeton == 3:
            if board[x][y+jeton-1] == 0 or board[x][y+jeton-1] == id:
              align += 1
          else:
            if board[x][y+jeton-1] == 0 or board[x][y+jeton-1] == id or board[x][y+jeton+1] == 0 or board[x][y+jeton+1] == id:
              align += 1
      if align == 4:
        align = 10000
      score += align
  # Pour les diagos croissantes
  x_tab = [0, 0, 0, 1, 2, 3]
  y_tab = [2, 1, 0, 0, 0, 0]
  for i in range(len(x_tab)):
    x = x_tab[i]
    y = y_tab[i]
    align = 0
    for jeton in range(4):
      if board[x+jeton][y+jeton] == id:
        if jeton == 0:
          if board[x+jeton+1][y+jeton+1] == 0 or board[x+jeton+1][y+jeton+1] == id:
            align += 1
        elif jeton == 3:
          if board[x+jeton-1][y+jeton-1] == 0 or board[x+jeton-1][y+jeton-1] == id:
            align += 1
        else:
          if board[x+jeton-1][y+jeton-1] == 0 or board[x+jeton-1][y+jeton-1] == id or board[x+jeton+1][y+jeton+1] == 0 or board[x+jeton+1][y+jeton+1] == id:
            align +=1
      if align == 4:
        align = 10000
      score += align
  # Pour les diagos decroissantes
  x_tab = [3, 4, 5, 6, 6, 6]
  y_tab = [0, 0, 0, 0, 1, 2]
  for i in range(len(x_tab)):
    x = x_tab[i]
    y = y_tab[i]
    align = 0
    for jeton in range(4):
      if board[x-jeton][y+jeton] == id:
        if jeton == 0:
          if board[x-jeton-1][y+jeton+1] == 0 or board[x-jeton-1][y+jeton+1] == id:
            align += 1
        elif jeton == 3:
          if board[x-jeton+1][y+jeton-1] == 0 or board[x-jeton+1][y+jeton-1] == id:
            align += 1
        else:
          if board[x-jeton+1][y+jeton-1] == 0 or board[x-jeton+1][y+jeton-1] == id or board[x-jeton-1][y+jeton+1] == 0 or board[x-jeton-1][y+jeton+1] == id:
            align += 1
      if align == 4:
        align = 10000
      score += align
      
  return score

def isFull(board, x):
   full = True
   for line in range(6):
      if board[x][line] == 0:
         full = False
   return full

def getColToplay():
  col_to_play = None
  delta = 0
  son_min = 10000000
  col_son_min = None
  for x1 in range(7):
     global_col_me = 0
     global_col_other = 0
     if isFull(board, x1):
        continue
     print("----------> Si je joue en " + str(x1))
     board_simu = board
     line_x1 = getLast(x1, board_simu)
     board_simu[x1][line_x1] = me
     for x2 in range(7):
        if isFull(board, x2):
          continue
        print("----------> Si il joue en " + str(x2))
        line_x2 = getLast(x2, board_simu)
        board_simu[x2][line_x2] = other
        mon_score = getScore(board_simu, me)
        son_score = getScore(board_simu, other)
        global_col_me += mon_score
        global_col_other += son_score
        print(mon_score, son_score)
        board_simu[x2][line_x2] = 0
     if global_col_other < son_min:
        son_min = global_col_other
        col_son_min = x1
     if global_col_me-global_col_other > delta:
        delta = global_col_me-global_col_other
        col_to_play = x1
     board_simu[x1][line_x1] = 0

  if col_to_play == None:
    col_to_play = col_son_min
  print("A jouer --> " + str(col_to_play))
  return col_to_play

while True:
  response = socket.recv(2048)
  payload = json.loads(response)
  if payload["type"] == "START":
    to_me = payload["play"]
    me = payload["you"]
    other = payload["other"]
    if to_me:
      send({'action': 'play', 'column': '3'})
  if payload["type"] == "PLAY_INFO":
    to_me = payload["play"]
    board = payload['payload']
    if to_me:
      send({'action': 'play', 'column': str(getColToplay())})
  if payload["type"] == "END":
    print("Gagné : " + str(payload["win"]))
    break


socket.close()