# Tyler Yere
# COMP 429
# HW2
# TicTacToeEngine.py

class TicTacToeEngine:
    def __init__(self):
        # board is just a list of dashes for blanks. X and O's will fill it eventually.
        self.board = ['-','-','-','-','-','-','-','-','-']
        # is it x's turn?
        self.x_turn = True
        # how many successful turns have we played?
        self.turns = 0
        

    def restart(self):
        self.board = ['-','-','-','-','-','-','-','-','-']
        self.x_turn = True
        self.turns = 0


    def display_board(self):
        j = 0
        for i in range(0,9): # for (i = 0; i < 9; i++) 
            # print without a new line
            print(self.board[i], end=' ') 
            j += 1
            # add a new line every 3 board spaces
            if j % 3 == 0:
                print('')
    
    
    def is_game_over(self):
        # winning combos in tic tac toe
        winning_combos = [  (0,1,2),(3,4,5),(6,7,8),
                            (0,3,6),(1,4,7),(2,5,8),
                            (0,4,8),(2,4,6)]

        # for each of the winning combos
        for combo in winning_combos:
            # assume the first piece is a winner
            winner = self.board[combo[0]]
            # if it is not blank
            if winner is 'X' or winner is 'O':
                # and if the next two on the board are the same as the first one
                if winner is self.board[combo[1]] and winner is self.board[combo[2]]:
                    # that piece has won
                    return winner

        # no winning combos and the board is full.
        if self.turns == 9:
            return 'T'
        
        # not done yet
        return '-'


    def make_move(self, pos):
        # make a move if it is valid (between 0 and 8 inclusive) 
        # increase number of turns by 1
        # invert the x_turn boolean
        if self.is_move_valid(pos):
            if self.x_turn:
                self.board[pos] = 'X'
            else:
                self.board[pos] = 'O'
            self.turns += 1
            self.x_turn = not self.x_turn

    
    def is_move_valid(self, pos):
        # make sure it is on the board and no one has already plkayed there!
        return (pos >= 0 and pos <= 8 and self.board[pos] is '-')