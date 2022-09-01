import os
import random
import sys
import pygame
from pygame.rect import Rect

pygame.init()
pygame.display.set_caption("Haze and Josh's Indian Ludo Project")
screenx = 800
screeny = 568
screen = pygame.display.set_mode((screenx, screeny), 16)

black = (0, 0, 0)
white = (255, 255, 255)
grey = (220, 220, 220)

bluepanel = (135, 206, 250)
greenpanel = (152, 251, 152)
yellowpanel = (255, 255, 51)
pinkpanel = (255, 192, 203)
redpanel = (255, 0, 0)
piece_colours = [(25, 25, 112), (0, 100, 0), (199, 21, 133), (102, 102, 0)]

current_path = os.path.dirname(__file__)
c280_path = os.path.join(current_path, 'c280_path')
GAME_FONT = pygame.freetype.Font(c280_path+'/'+'conthrax-sb.ttf', 22)
overlay = pygame.image.load(os.path.join(c280_path, 'overlay.png')).convert_alpha()
overlay.set_alpha(95)
default_roll = pygame.image.load(os.path.join(c280_path, 'roll1.png')).convert_alpha()
bluerolls = [pygame.image.load(os.path.join(c280_path, f'blueroll{i+1}.png')).convert_alpha() for i in range(4)]
greenrolls = [pygame.image.load(os.path.join(c280_path, f'greenroll{i+1}.png')).convert_alpha() for i in range(4)]
pinkrolls = [pygame.image.load(os.path.join(c280_path, f'pinkroll{i+1}.png')).convert_alpha() for i in range(4)]
yellowrolls = [pygame.image.load(os.path.join(c280_path, f'yellowroll{i+1}.png')).convert_alpha() for i in range(4)]
rolls = [bluerolls, greenrolls, pinkrolls, yellowrolls]


class Board:
    def __init__(self):
        self.board = []
        self.players = [Player(1), Player(2), Player(3), Player(4)]
        self.set_up_board()
        self.end = self.board[2][2]
        self.end.is_safe_spot = True
        self.turn = 0
        self.ranks = []

    def check_rankings(self):  # Checks if player finished and assigns their rank
        for player in self.players:
            if player not in self.ranks:
                if all([i.finished for i in player.counters]):  # If all counters for a player is finished, add to ranking
                    self.ranks.append(player)

    def display_visuals(self):  # Draws the board and displays the gui to the user
        blue_spaces = [(37, 25), (20, 9), (37, 9), (54, 9)]
        pink_spaces = [(37, 50), (20, 67), (37, 67), (54, 67)]
        yellow_spaces = [(25, 37), (9, 20), (9, 37), (9, 54)]
        green_spaces = [(50, 37), (67, 20), (67, 37), (67, 54)]
        piece_positions = [yellow_spaces, pink_spaces, green_spaces, blue_spaces]
        colours = [redpanel, bluepanel, pinkpanel, greenpanel, yellowpanel]
        matches = [[2, 2], [0, 2], [4, 2], [2, 4], [2, 0]]
        for row in range(5):
            for col in range(5):
                x, y = (((row + 1) * 75) + 300), ((col + 1) * 75)
                if [row, col] in matches:
                    pygame.draw.rect(screen, colours[matches.index([row, col])], Rect(x, y, 75, 75))  # Color special spaces
                    pygame.draw.line(screen, black, (x, y), (x + 74, y + 74))
                    pygame.draw.line(screen, black, (x + 74, y), (x, y + 74))
                else:
                    pygame.draw.rect(screen, grey, Rect(x,  y, 75, 75))
                if self.board[col][row].contains:
                    for coin in self.board[col][row].contains:  # Board space contains player piece
                        draw = piece_positions[self.players.index(coin.owner)][coin.get_counter_num()]
                        coin.collision = pygame.Rect(x + draw[0]-8, y + draw[1]-8, 15, 15)  # Collision for interaction with counters and mouse
                        pygame.draw.circle(screen, piece_colours[self.players.index(coin.owner)],
                        (x + draw[0], y + draw[1]), 6)
                pygame.draw.rect(screen, black, Rect(x, y, 75, 75), 1)

    def take_turn(self):
        self.turn += 1
        if self.turn > 3:
            self.turn = 0

    def set_up_board(self):  # Init board
        for x in range(5):
            temp = []
            for y in range(5):
                temp.append(Panel())
            self.board.append(temp)
        for i in range(4):
            self.pathing(self.players[i], i)

    def move_counter(self, counter, dice_roll):
        counter.owner.dice_roll = dice_roll
        flag = False
        if not counter.owner.has_killed:  # Gateway check
            for num in range(1, dice_roll+1):
                temp = counter.current_panel+num
                # If player has not killed and is at gateway they should not move forward until one step behind gateway
                if temp <= len(counter.owner.route):
                    if counter.owner.route[temp] is counter.owner.gateway and not counter.owner.has_killed and not flag:
                        temp1 = counter.current_panel+num-1
                        counter.owner.route[counter.current_panel].contains.remove(counter)
                        counter.current_panel = temp1
                        counter.owner.route[temp1].contains.append(counter)
                        print(f"{counter.owner.name} at gateway.")
                        flag = True
                else:
                    pass

        if not flag:             # Movement
            counter.owner.route[counter.current_panel].contains.remove(counter)
            if counter.current_panel + dice_roll >= len(counter.owner.route):
                counter.current_panel = len(counter.owner.route)-1
            else:
                counter.current_panel += dice_roll
            counter.owner.route[counter.current_panel].contains.append(counter)
            if counter.owner.route[counter.current_panel] is self.board[2][2]:  # Player is at final spot, counter is finished
                counter.finished = True
        for encounter in counter.owner.route[counter.current_panel].contains:  # Checks if piece is on opponent
            if encounter is not counter and not counter.owner.route[counter.current_panel].is_safe_spot and encounter.owner is not counter.owner:
                encounter.current_panel = 0
                counter.owner.route[counter.current_panel].contains.remove(encounter)
                encounter.owner.route[0].contains.append(encounter)
                counter.owner.has_killed = True
                self.reset_roll(counter)
                return
        if dice_roll == 4 and not flag:  # Extra Turn from Dice Roll
            self.reset_roll(counter)
            return
        counter.owner.dice_roll = 0  # End of turn
        counter.owner.turn_finished = True

    def reset_roll(self, counter):
        global usable_pieces, piece_collisions
        counter.owner.dice_roll = 0
        counter.owner.turn_finished = False
        usable_pieces = []
        piece_collisions = []

    def dice_roll(self):
        roll = random.randint(1, 4)
        return roll

    def pathing(self, player, index):
        players_start = [[2, 0], [4, 2], [2, 4], [0, 2]]  # Defines each players path they take around the board
        start = players_start[index]
        player.route.append(self.board[start[0]][start[1]])
        player.set_up_counters(self.board[start[0]][start[1]])
        self.board[start[0]][start[1]].is_safe_spot = True
        functions_list = \
        [(self.move_down, 2), (self.move_right, 4), (self.move_up, 4), (self.move_left, 4), (self.move_down, 1), (self.move_right, 3), (self.move_down, 2), (self.move_left, 2), ("gateway", 1), (self.move_up, 1),
         (self.move_right, 1)],\
        [(self.move_right, 2), (self.move_up, 4), (self.move_left, 4), (self.move_down, 4), (self.move_right, 1), (self.move_up, 3), (self.move_right, 2), (self.move_down, 2), ("gateway", 1), (self.move_left, 1),
         (self.move_up, 1)],\
        [(self.move_up, 2), (self.move_left, 4), (self.move_down, 4), (self.move_right, 4), (self.move_up, 1), (self.move_left, 3), (self.move_up, 2), (self.move_right, 2), ("gateway", 1), (self.move_down, 1),
         (self.move_left, 1)],\
        [(self.move_left, 2), (self.move_down, 4), (self.move_right, 4), (self.move_up, 4), (self.move_left, 1), (self.move_down, 3), (self.move_left, 2), (self.move_up, 2), ("gateway", 1), (self.move_right, 1),
         (self.move_down, 1)]
        for func in functions_list[index]:
            for _ in range(func[1]):
                if not isinstance(func[0], str):
                    start = func[0](start)
                    player.route.append(self.board[start[0]][start[1]])
                else:
                    player.gateway = self.board[start[0]][start[1]]

    def move_right(self, input): # Functions for player movement
        return [input[0], input[1]+1]

    def move_left(self, input):
        return [input[0], input[1]-1]

    def move_up(self, input):
        return [input[0]-1, input[1]]

    def move_down(self, input):
        return [input[0] + 1, input[1]]


class Panel:
    def __init__(self):
        self.is_safe_spot = False
        self.contains = []


class Player:
    def __init__(self, player_num):
        self.name = f"Player {player_num}"
        self.route = []
        self.gateway = None
        self.has_killed = False
        self.counters = []
        self.dice_roll = 0
        self.turn_finished = False

    def set_up_counters(self, panel): # Initialise counters position
        for _ in range(4):
            temp = Counter(self)
            self.counters.append(temp)
            panel.contains.append(temp)


class Counter:
    def __init__(self, player):
        self.owner = player
        self.current_panel = 0
        self.finished = False
        self.collision = []

    def get_counter_num(self): # User has 4 counters and each has their own identity
        return self.owner.counters.index(self)


if __name__ == '__main__':
    board = Board()
    dice_collision = pygame.Rect(50, 70, 140, 120)
    usable_pieces = []
    piece_collisions = []
    while True:
        board.check_rankings()
        if board.players[board.turn].turn_finished or board.players[board.turn] in board.ranks:  # If a player's turn has ended or player has all pieces in the middle
            board.players[board.turn].turn_finished = False
            board.take_turn()
            usable_pieces = []
            piece_collisions = []
        if len(board.ranks) >= 3:  # Game ends when 3 players are in the rankings
            is_running = False
            sys.exit()
        screen.fill((255, 255, 224))  # Resets the canvas to bg colour
        board.display_visuals()
        for event in pygame.event.get():  # Checks for mouse movements and button presses
            mouse = pygame.Rect(0, 0, 15, 15)
            mouse.center = pygame.mouse.get_pos()   # Keeps track of mouse movement
            if event.type == pygame.QUIT:
                is_running = False
                sys.exit()
            elif event.type == pygame.KEYDOWN:

                if event.key == pygame.K_F2:
                    board.test_case()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if mouse.colliderect(dice_collision):  # Checks if the mouse is in contact with the dice image
                    if pygame.mouse.get_pressed()[0] and board.players[board.turn].dice_roll == 0:  # Checks if a dice hasn't been rolled and left clicked
                        board.players[board.turn].dice_roll = board.dice_roll()
                        for piece in board.players[board.turn].counters:
                            if not piece.finished:  # Checks if a player's counter hasn't finished
                                if piece.owner.route[piece.current_panel + 1] != piece.owner.gateway:  # Checks if the counter isn't next to a gateway
                                    usable_pieces.append(piece)
                                    piece_collisions.append(piece.collision)
                                elif piece.owner.route[piece.current_panel + 1] is piece.owner.gateway and piece.owner.has_killed:  # If a player's coin has taken another coin allow passage through gateway
                                    if piece.current_panel + board.players[board.turn].dice_roll <= len(
                                            piece.owner.route):  # Check to make sure the counter can't go past the final spot
                                        usable_pieces.append(piece)
                                        piece_collisions.append(piece.collision)
                elif mouse.collidelist(piece_collisions) >= 0:  # Checks if mouse is ion contact with the current player's coin
                    counter_num = usable_pieces[mouse.collidelist(piece_collisions)].get_counter_num()
                    board.move_counter(board.players[board.turn].counters[counter_num], board.players[board.turn].dice_roll)  # Move the coin based on the dice roll
        if board.players[board.turn].dice_roll != 0:  # Displays current dice roll result
            screen.blit(rolls[board.players.index(board.players[board.turn])][board.players[board.turn].dice_roll - 1], (50, 70))
            text_surface, rect = GAME_FONT.render("Select a coin to move", black)
            screen.blit(text_surface, (20, 210))
        else:  # Displays a greyed out dice
            screen.blit(default_roll, (50, 70))
            text_surface, rect = GAME_FONT.render("Click on dice to roll", black)
            screen.blit(text_surface, (20, 210))
        text_surface, rect = GAME_FONT.render((board.players[board.turn].name+"'s Turn"), black)  # Display's current player's turn
        screen.blit(text_surface, (20, 20))
        board.display_visuals()
        screen.blit(pygame.transform.rotate(overlay, (board.turn * 90)), (375, 75))  # Displays overlay
        if board.ranks:  # Displays rankings
            for i in range(len(board.ranks)):
                text_surface, rect = GAME_FONT.render((f"Rank {i+1}: "+board.ranks[i].name), black)
                screen.blit(text_surface, (20, 300+((i+1)*30)))
        pygame.display.flip()  # Draws everything to screen
