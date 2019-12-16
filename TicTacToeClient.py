# Tyler Yere, Network Cowboy

import argparse, socket, logging

# Comment out the line below to not print the INFO messages
# logging.basicConfig(level=logging.INFO)

def recvall(sock, length):
    data = b''
    while len(data) < length:
        more = sock.recv(length - len(data))
        if not more:
            logging.error('Did not receive all the expected bytes from server.')
            break
        data += more
    return data


# correctly formats the board update strings from the server to be presented to the user
def parse_board_update(board_string):
    for i in range(len(board_string)):
        if i % 3 == 0:
            print()
        print(board_string[i], end = ' ')
    print()


def client(host,port):
    # connect
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host,port))
    logging.info('Connect to server: ' + host + ' on port: ' + str(port))
    player_symbol = None

    # three way handshake / connect to server
    sock.sendall(b'00')     # CONNECT
    message = recvall(sock, 2).decode('utf-8')
    if message.startswith('02'): # we can choose between X or O
        logging.info('we can now choose X or O')
        player_symbol = input('choose X or O: ')
        while player_symbol != 'X' and player_symbol != 'O':
            player_symbol = input('choose X or O: ')
        sock.sendall(b'01 ' + player_symbol.encode('utf-8'))    # CHOOSE [X|O]
        print("You are: " + player_symbol)
        logging.info("Client side, player symbol: " + recvall(sock, 2).decode('utf-8')[1])
    else:   # we cannot receive messages of different lengths; must somehow compress into one uniform length
        player_symbol = message[1]
        print("You have been assigned: " + player_symbol)
        logging.info("Client side, player symbol: " + message[1])

    # wait until we get signaled that the game is starting
    message = recvall(sock, 2).decode('utf-8')
    logging.info("Received " + message + " from the server")

    # playtime
    board_update = recvall(sock, 12).decode('utf-8')
    board_string = board_update[3:]
    parse_board_update(board_string)

    # see which player has their turn first
    message = recvall(sock, 2).decode('utf-8')
    logging.info("Received " + message + " from the server")

    # while we have not received a game over message yet
    while True:
        if message.startswith('11'):
            message = message + recvall(sock, 2).decode('utf-8')
            if player_symbol == message[3]:
                print(player_symbol, end = ": ")
                player_move = input('Choose move [0-8]: ')
                while not player_move.isdigit() or 9 < int(player_move) < 0:
                    print(player_symbol, end = ": ")
                    player_move = input('Choose move [0-8]: ')
                sock.sendall(b'10 ' + player_move.encode('utf-8'))
            else:
                other_player = 'X' if player_symbol == 'O' else 'O'
                print("Waiting for player " + other_player)
        elif message.startswith('13'):
            # receive the rest of the board update if the message notifies us of an update
            board_update = message + recvall(sock, 10).decode('utf-8')
            board_string = board_update[3:]
            parse_board_update(board_string)
        elif message.startswith('14'):
            # break if server sends game over message
            break

        message = recvall(sock, 2).decode('utf-8')

    logging.info("Server has indicated that the game is over!")

    # receive message on who won and loss
    message = recvall(sock, 2).decode('utf-8')
    if message == '20':
        print('You Won!')
    elif message == '21':
        print('You Lost :(')
    else:
        print('Tie!')

    # get booted off server
    bye = recvall(sock, 2).decode('utf-8')
    if bye == '22':
        print("You have been disconnected from the server")
    else:
        print("ERROR: Bad message from server")

    # quit
    sock.close()


if __name__ == '__main__':
    port = 9001

    parser = argparse.ArgumentParser(description='Tic Tac Oh No Client (TCP edition)')
    parser.add_argument('host', help='IP address of the server.')
    args = parser.parse_args()

    client(args.host, port)
    