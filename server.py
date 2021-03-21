import sys, socket, time
from baseclasses import Game


if len(sys.argv) != 3:
    print('Please enter IP and port')
    sys.exit()

IP = str(sys.argv[1])
PORT = int(sys.argv[2])
HEADER_LENGTH = 5
COLORS = {
    '0': 'brown',
    '1': 'white',
    '2': 'red',
    '3': 'green',
    '4': 'blue',
}

SERVER_SOCKET = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
SERVER_SOCKET.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
SERVER_SOCKET.bind((IP, PORT))
SERVER_SOCKET.listen()

players_sockets = []
players_names = []

print(f'Listening for connections on {IP}:{PORT}...')


def new_connection(client_socket, client_address):
    if len(players_sockets) >= 2:
        return False
    # player should send his name
    username = client_socket.recv(1024).decode('utf-8')
    # player disconnected before he sent his name
    if not username:
        return False
    players_sockets.append(client_socket)
    players_names.append(username)
    print('Accepted new connection from {}:{}, username: {}'.format(*client_address, username))
    return True

def send_message(client_socket, message: str):
    message = message.encode('utf-8')
    message_header = f"{len(message):<{HEADER_LENGTH}}".encode('utf-8')
    client_socket.send(message_header + message)

def recieve_message(client_socket):
    try:
        message_header = client_socket.recv(HEADER_LENGTH)
        if not message_header:
            print('connection lost')
            client_socket.close()
            index = players_sockets.index(client_socket)
            del players_sockets[index]
            return False
        message_length = int(message_header.decode('utf-8').strip())
        message = client_socket.recv(message_length).decode('utf-8')
        return message
    except IOError:
        return False


while True:
    try:
        connection = SERVER_SOCKET.accept()
        new_connection(*connection)
    except KeyboardInterrupt:
        print('\nServer shutdown')
        SERVER_SOCKET.close()
        sys.exit()

    if len(players_sockets) == 2:
        game = Game(players_names)
        game.lay_out_all()
        init_state = game.encode_state()
        for i in range(len(players_sockets)):
            send_message(players_sockets[i], str(i) + init_state)
            time.sleep(1)
        break


cur_p_id = 0
block = False
while True:
    if len(players_sockets) < 2:
        print('shutdown')
        break
    req = recieve_message(players_sockets[cur_p_id])
    if not req:
        continue
    if req[0] == '0' and not block:
        i, j = list(req[1:])
        res = game.buy_board_card((int(i), int(j)))
    if req[0] == '1' and not block:
        res = game.take_two_gems(COLORS[req[1]])
    if req[0] == '2' and not block:
        colors = [COLORS[i] for i in req[1:]]
        res = game.take_three_gems(colors)
    if req[0] == '3':
        block = False
        cur_p_id = (cur_p_id + 1) % 2
        game.end_turn_checks()
        for player in players_sockets:
            state = game.encode_state()
            send_message(player, state)
        continue
    if res and not block:
        send_message(players_sockets[cur_p_id], game.encode_state())
        block = True
    else:
        send_message(players_sockets[cur_p_id], 'False')
