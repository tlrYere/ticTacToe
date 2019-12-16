# Tyler Yere, Network Cowboy

import concurrent.futures, argparse, socket, logging, threading, TicTacToeEngine, random

# Comment out the line below to not print the INFO messages
# logging.basicConfig(level=logging.INFO)

class ClientThread(threading.Thread):
    def __init__(self, address, socket, client_number):
        threading.Thread.__init__(self)
        self.csock = socket
        logging.info('New connection added.')
        self.client_number = client_number
        self.chosen_symbol = None
    

    def register(self, leftover_symbol):
        # REGISTRATION PHASE
        message = self.recvall(2)
        msg = message.decode('utf-8')
        logging.info('Recieved a message from client: ' + msg)

        if self.client_number == 1:  # if this is the first client to connect
            if msg.startswith('00'):
                self.csock.sendall(b'02')   # CHOOSE sent to client
                logging.info('Recieved 02 CONNECT from client.')
            else:
                self.csock.sendall(b'061 REJECT')
                logging.warning('Bad request from client.')

            # CHOOSE [X|O]
            message = self.recvall(4).decode('utf-8')
            if message.startswith('01'):
                self.chosen_symbol = message[3]
            else:
                logging.warning('Bad request from client')

            # ASSIGN [X|O]
            self.csock.sendall(b'0' + self.chosen_symbol.encode('utf-8'))
        else:   # this is client #2, the second one to connect
            if msg.startswith('00'):
                logging.info('Recieved 02 CONNECT from client.')
            else:
                self.csock.sendall(b'061 REJECT')
                logging.warning('Bad request from client.')

            self.chosen_symbol = leftover_symbol

            # ASSIGN [X|O]
            self.csock.sendall(b'0' + self.chosen_symbol.encode('utf-8'))

        logging.info('Registration for client # '+ str(self.client_number) +' complete')
        logging.info('Client #' + str(self.client_number) + ' symbol: ' + self.chosen_symbol)


    # signals start of the game to each client which in turn notifies the client user
    def signal_start(self):
        # START 05
        self.csock.sendall(b'05')
    

    def recvall(self, length):
        data = b''
        while len(data) < length:
            more = self.csock.recv(length - len(data))
            if not more:
                logging.error('Did not receive all the expected bytes from client.')
                break
            data += more
        return data


    def disconnect(self):   # disconnects client from server 
        self.csock.close()
        logging.info('Disconnect client.')
        print("Disconnect client.")


def listen_for_clients(port, sock, client_number):
    sock.listen(1)
    logging.info('Server is listening on port ' + str(port))
    print("Server is now awaiting for connections on port " + str(port))

    sc,sockname = sock.accept()
    if client_number > 2:   # there are already two clients connected to the server playing tic tac toe
        sock.close()
        return
    logging.info("Accepted connection.")
    print("Accepted connection.")
    return ClientThread(sockname, sc, client_number)


# whose_turn is either 'X' or 'O'
def signal_turn_to_clients(thread1, thread2, whose_turn):
    thread1.csock.sendall(b'11 ' + whose_turn.encode('utf-8'))
    thread2.csock.sendall(b'11 ' + whose_turn.encode('utf-8'))


# whose_turn is either 'X' or 'O'
def read_move_from_correct_client(thread1, thread2, whose_turn):
    if thread1.chosen_symbol == whose_turn:
        return thread1.recvall(4).decode('utf-8')
    else:
        return thread2.recvall(4).decode('utf-8')


# sends board update in a string for the client to parse and present to the user
def send_board_updates(thread1, thread2, game):
    separator = ''
    thread1.csock.sendall(b'13 ' + separator.join(game.board).encode('utf-8'))
    thread2.csock.sendall(b'13 ' + separator.join(game.board).encode('utf-8'))


def signal_clients_game_over(thread1, thread2):
    thread1.csock.sendall(b'14')
    thread2.csock.sendall(b'14')


def signal_winner_to_clients(thread1, thread2, winner):
    if thread1.chosen_symbol == winner:
        thread1.csock.sendall(b'20')    # 20 WON
        thread2.csock.sendall(b'21')    # 21 LOST
    elif thread2.chosen_symbol == winner:
        thread2.csock.sendall(b'20')
        thread1.csock.sendall(b'21')
    else:
        thread1.csock.sendall(b'15')    # TIE!
        thread2.csock.sendall(b'15')


def kick_clients(thread1, thread2):
    thread1.csock.sendall(b'22')
    thread1.disconnect()
    thread2.csock.sendall(b'22')
    thread2.disconnect()
        

def server():
    # start serving (listening for clients)
    port = 9001
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind(('localhost',port))

    while True:
        # REGISTRATION PHASE
        # VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
        num_of_clients = 1
        leftover_symbol = None

        # first client has connected
        t1 = listen_for_clients(port, sock, num_of_clients)
        t1.register(leftover_symbol)

        # set leftover symbol before next client connects
        if t1.chosen_symbol == 'X':
            leftover_symbol = 'O'
        else:   # first client chose O
            leftover_symbol = 'X'

        num_of_clients+=1

        # second client has connected
        t2 = listen_for_clients(port, sock, num_of_clients)
        t2.register(leftover_symbol)
        num_of_clients+=1

        # signal to the clients that the game is starting
        t1.signal_start()
        t2.signal_start()

        # PLAYTIME PHASE
        # VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
        game = TicTacToeEngine.TicTacToeEngine()
        game.display_board()

        # NOTE: server randomly chooses which player goes first
        game.x_turn = bool(random.getrandbits(1))

        # send board update to clients here
        send_board_updates(t1, t2, game)

        # let each client know whose turn it is (first turn)
        if game.x_turn:
            logging.info("it is X's turn!")
            signal_turn_to_clients(t1, t2, 'X')
        else:
            logging.info("it is O's turn!")
            signal_turn_to_clients(t1, t2, 'O')

        # now, listen for the correct player to return a valid move
        while True:
            logging.info("before reading first move")
            move = read_move_from_correct_client(t1, t2, 'X') if game.x_turn else read_move_from_correct_client(t1, t2, 'O')
            logging.info("after reading first move")

            if move.startswith('10'):
                move_index = int(move[3])       # indicates actual index current user has chosen
                while not(game.is_move_valid(move_index)):  # while move is not valid, keep asking for input from the correct client
                    signal_turn_to_clients(t1, t2, 'X') if game.x_turn else signal_turn_to_clients(t1, t2, 'O')
                    move = read_move_from_correct_client(t1, t2, 'X') if game.x_turn else read_move_from_correct_client(t1, t2, 'O')
                    move_index = int(move[3])
                print('X chose ' + str(move_index)) if game.x_turn else print('O chose ' + str(move_index))
                game.make_move(move_index)
                game.display_board()
                print()
                send_board_updates(t1, t2, game)
                if game.is_game_over() != "-":
                    winner = game.is_game_over()
                    print("GAME IS OVER")
                    break
            else:
                logging.info("Bad request from client")

            signal_turn_to_clients(t1, t2, 'X') if game.x_turn else signal_turn_to_clients(t1, t2, 'O')

        # POSTGAME PHASE
        # VVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVVV
        signal_clients_game_over(t1, t2)
        signal_winner_to_clients(t1, t2, winner)
        kick_clients(t1, t2)

    # note: only way to actually kill the server is Ctrl+C on the command line
    print("Server killed")


if __name__ == '__main__':
    server()
    logging.info('Game over!')