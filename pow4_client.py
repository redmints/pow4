import socket
import sys
import json
from copy import deepcopy

m_hote = "localhost"
m_port = 2023
m_full_align_score = 10000
m_max_depth = 4

m_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
m_socket.connect((m_hote, m_port))
m_to_me = False
m_board = None
m_me = None
m_other = None

def send(obj):
   message = json.dumps(obj)
   m_socket.send(message.encode())

def get_last(x, board):
  y = 0
  res = board[x][0]
  while res != 0:
    y += 1
    assert y <= 5
    res = board[x][y]
  return y


# calcul du score d'un alignement de 4
def get_one_align_score(board, x_init, y_init, x_shift, y_shift, id):
  score = 0
  x_len = len(board)
  y_len = len(board[0])
  x = x_init
  y = y_init

  # on parcourt un alignement
  for shift in range(4):
    # on verifie qu'on ne sort pas de la grille
    if (x >= x_len) or (x < 0) or (y >= y_len) or (y < 0):
      # si on sort, on arrete le traitement et on signale la sortie de grille
      score = None
      break
    else:
      # on ne sort pas, on peut analyser le jeton
      val = board[x][y]
      if val == 0:
        # on n'augmente pas le score mais on ne considere pas l'alignement a 4 impossible
        pass
      elif val == id:
        score += 1
      else:
        # un jeton de l'adversaire est dans l'alignement, on arrete et on retourne 0
        score = 0
        break

    # on se deplace sur le prochain jeton
    x += x_shift
    y += y_shift

  # ajustement du score
  if score is not None:
    if score == 4:
      score = m_full_align_score   # jackpot
    else:
      score *= 2      # on favorise un alignement plutot que des jetons isoles

  return score


# calcul du score de tous les alignements sur un meme axe
def get_one_dimension_score(board, x_init, y_init, x_shift, y_shift, id):
  score = 0
  x = x_init
  y = y_init

  while True:
    res = get_one_align_score(board, x, y, x_shift, y_shift, id)
    if res is None:
      # on est arrive a la fin de l'axe
      break
    else:
      score += res
      x += x_shift
      y += y_shift

  return score


# calcul du score de tous les alignements sur tous les axes
def get_score(board, id):
  score = 0
  x_len = len(board)
  y_len = len(board[0])

  # pour les lignes
  for y in range(y_len):
    score += get_one_dimension_score(board, 0, y, 1, 0, id)
  
  # pour les colonnes
  for x in range(x_len):
    score += get_one_dimension_score(board, x, 0, 0, 1, id)

  # pour les diagos croissantes
  x_tab = [0, 0, 0, 1, 2, 3]
  y_tab = [2, 1, 0, 0, 0, 0]
  for i in range(len(x_tab)):
    score += get_one_dimension_score(board, x_tab[i], y_tab[i], 1, 1, id)

  # pour les diagos decroissantes
  x_tab = [3, 4, 5, 6, 6, 6]
  y_tab = [0, 0, 0, 0, 1, 2]
  for i in range(len(x_tab)):
    score += get_one_dimension_score(board, x_tab[i], y_tab[i], -1, 1, id)

  return score


def is_full(board, x):
  full = True
  if board[x][5] == 0:
    full = False
  return full


# calcule le score lorsqu'on joue a une position
def get_play_score(board, position, player, other, depth):
  # on ne peut jouer que s'il reste de la place
  if is_full(board, position):
    return None

  # on place le jeton dans un nouveau tableau
  new_board = deepcopy(board)
  new_board[position][get_last(position, board)] = player

  # calcul du nouveau score du joueur
  score = 0
  end = False
  player_score = get_score(new_board, player)
  if player_score >= m_full_align_score:
    # si le joueur a gagne, on arrete de jouer, pas besoin de calculer le score de l'autre
    end = True
    score = player_score
  else:
    other_score = get_score(new_board, other)
    # on deduit le score de l'autre pour que le score global indique si le jeton profite plus au joueur qu'a l'autre
    score = player_score - other_score

  # si le joueur est l'autre, on inverse le score car un bon score pour l'autre est un mauvais score pour moi
  if player == m_other:
    score = -score

  # on augmente le poids des coups proches pour pouvoir converger plus rapidement
  assert m_max_depth - depth > 0
  score = score * ((m_max_depth - depth) ** 2)

  # on continue de jouer si la partie n'est pas terminee et si la profondeur max n'est pas atteinte
  depth += 1
  if (not end) and (depth < m_max_depth):
    # on passe a l'autre joueur, on le fait jouer sur toutes les colonnes
    # et on accumule le score
    for x in range(len(new_board)):
      pos_score = get_play_score(new_board, x, other, player, depth)  # appel recursif
      if pos_score is not None:
        score += pos_score

  return score


def get_col_to_play():
  col_to_play = None
  max_score = -999999999

  for x in range(len(m_board)):
    score = get_play_score(m_board, x, m_me, m_other, 0)
    if score is not None:
      print("col = " + str(x) + " score = " + str(score))
      if score > max_score:
        max_score = score
        col_to_play = x
    else:
      print("colonne " + str(x) + " pleine")

  assert col_to_play is not None
  print("=> colonne choisie = " + str(col_to_play))
  return col_to_play


while True:
  response = m_socket.recv(2048)
  payload = json.loads(response)
  if payload["type"] == "START":
    m_to_me = payload["play"]
    m_me = payload["you"]
    m_other = payload["other"]
    if m_to_me:
      send({'action': 'play', 'column': '3'})
  if payload["type"] == "PLAY_INFO":
    m_to_me = payload["play"]
    m_board = payload['payload']
    if m_to_me:
      send({'action': 'play', 'column': str(get_col_to_play())})
  if payload["type"] == "END":
    print("Gagné : " + str(payload["win"]))
    break


m_socket.close()