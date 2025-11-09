from src.strategy import Strategy
import numpy as np
from abc import ABC, abstractmethod

# making an overall class for what a player should do
class Player(ABC):
    def __init__(self):
        self.hand = []
    
    @abstractmethod    
    def get_hand(self):
        pass

    @abstractmethod
    def new_hand(self, cards: list[int]):
        pass

    @abstractmethod
    def take_action(self):
        pass

# making an RLPlayer taking in the template of the player defined above
class RLPlayer(Player):
    def __init__(self, strategy: Strategy):
        self.hand = []
        self.strategy = strategy
        self.credits = 30
     
    def get_hand(self):
        return self.hand
    
    def new_hand(self, cards: list[int]):
        self.hand = cards

    def take_action(self, board):
        return self.strategy.chose_action(board, self.hand)

# this is for when a human wants to play
class HumanPlayer(Player):
    def __init__(self):
        self.hand = []
        self.credits = 50
     
    def get_hand(self):
        return self.hand
    
    def new_hand(self, cards: list[int]):
        self.hand = cards

    def take_action(self, board):
        while True:
            user_input = input("Your hand: {} | Board: {}\nChoose action: [c]all or [f]old? ".format(self.hand, board)).strip().lower()
            if user_input == 'c':
                return 0  # call
            elif user_input == 'f':
                return 1  # fold
            else:
                print("Invalid input. Please enter 'c' for call or 'f' for fold.")

# This is how i define a game, this class is primarily for simulation
class Game():
    def __init__(self, players: list[Player]):
        self.deck = [] # adding 4 of each card to the deck in the beginning of a game
        for j in range(1, 11): # of values 1-10 
            self.deck.extend([j, j, j, j]) #clubs, diamonds, hearts, spades
        self.board = []
        self.players = players
        for player in self.players: #giving players 2 cards 
            player.new_hand(cards = self.draw_cards(2))
        self.stake = 1
        self.t = 0
        # making the game keep track of the rewards for each player
        self.rewards = [[],[]] #keep track of rewards for each player.
        self.state_idxs = [[],[]]
        self.state_list_idxs = [[],[]]
        self.actions = [[],[]]
        for i in range(2): #updating the state list to follow the state trajectory
            state_idx = self.players[i].strategy._get_state_idx(self.players[i].hand, self.board)
            self.state_list_idxs[i].append(0)
            self.state_idxs[i].append(state_idx)

    # simulates one round of the game, first taking actions,
    #  then handing out rewards and updating each players value function using the n-step backup algorithm
    def simulate_one_round(self): 
        #each player takes an action
        for player_idx in range(2):
            action = self.players[player_idx].take_action(self.board)
            self.actions[player_idx].append(action)

        #check for actions
        if self.actions[0][-1] == 0 and self.actions[1][-1] == 0: #both keep on going
            if self.t != 3:
                for player_idx in range(2):
                    self.rewards[player_idx].append(0)
            end = False #keep on going
        elif self.actions[0][-1] == 1 and self.actions[1][-1] == 1: #both give up
            for player_idx in range(2):
                self.rewards[player_idx].append(0)
            end = True # we stop
        else:
            for player_idx in range(2): # one give up
                if self.actions[player_idx][-1] == 0:
                    self.rewards[player_idx].append(self.stake) #won
                else:
                    self.rewards[player_idx].append(-self.stake)  #gave up
            end = True # we stop

        # if we are on the last round: and both chose to continue
        if self.t == 3 and end == False: 
            hand0 = self.players[0].hand + self.board
            hand1 = self.players[1].hand + self.board
            winner, loser = self.get_winner([hand0, hand1])
            if winner != 2:
                self.rewards[winner].append(self.stake*2)
                self.rewards[loser].append(-self.stake*2)
            else:
                for i in range(2): self.rewards[i].append(0)
            end = True

        # actions have been taken so draw cards
        if end == False:
            self.draw_card_to_board()

        #we are now getting ready for the next round
        self.t += 1
        self.stake = self.stake * 2

        #update the states
        for player_idx in range(2):
            if end == True: # go to terminal state
                self.state_list_idxs[player_idx].append(4)#terminal
            else:
                state_idx = self.players[player_idx].strategy._get_state_idx(self.players[player_idx].hand, self.board)
                self.state_list_idxs[player_idx].append(self.t)
                self.state_idxs[player_idx].append(state_idx)
        #update values
        self.update_values(end)
        return end

    def update_values(self, end):
        if end == True: # we stop before t = n
            strategy = self.players[0].strategy
            for player in range(2):
                start_t = max(0, self.t - strategy.n)
                for i in range(start_t, self.t): # for each update we did not get to do fully
                    t_to_update = i
                    n = self.t - t_to_update # eg if we have n = 3, but t = 2, we can just set n = 2
                    strategy.make_value_update(self.rewards[player],
                                               self.state_idxs[player],
                                               self.state_list_idxs[player],
                                               self.actions[player],
                                               t_to_update, n = n)

        elif self.t - self.players[0].strategy.n >= 0:
            for player in range(2): # for each player update their action value functions
                t_to_update = self.t - self.players[0].strategy.n
                strategy = self.players[0].strategy
                strategy.make_value_update(self.rewards[player],
                                           self.state_idxs[player],
                                           self.state_list_idxs[player],
                                           self.actions[player],
                                           t=t_to_update, 
                                           n=strategy.n)
    # runs 4 simulated rounds for this game
    def simulate_game(self):
        for i in range(4): # 4 rounds
            end_by_action = self.simulate_one_round()
            if end_by_action == True:
                return
    
    #logic to draw a card
    def draw_cards(self, n):
        indices = np.random.choice(len(self.deck), size=n, replace=False)
        indices = sorted(indices, reverse=True)  # ensure correct deletion order
        cards = [self.deck[idx] for idx in indices]
        
        for card in indices:
            del self.deck[card]
        return cards
    
    def draw_card_to_board(self):
        self.board.extend(self.draw_cards(1))
    
    def get_unique(self, hand):
        return np.unique(hand, return_counts = True) # returns (unique_values, counts of these)

    #logic to decide who wins, if both players continues to the end
    def get_winner(self, hands):
        unique_hands = [self.get_unique(hand) for hand in hands]
        scores = [[],[]]
        for i, hand in enumerate(unique_hands):
            max_uniq = np.max(hand[1]) # is it a pair, 3 of a kind or 4 of a kind
            argmx = np.where(hand[1] == hand[1].max())[0][-1] # the right most argmax (if there is multiple)
            max_value = hand[0][argmx] # what value is the pair?
            scores[i].extend([max_uniq, max_value])

        if scores[0][0] > scores[1][0]: # 0 has more of the same kind
            return 0, 1
        elif scores[0][0] < scores[1][0]: # 1 has more of the same kind
            return 1, 0
        else: # they have the same amount of the same kind so check the values
            if scores[0][1] > scores[1][1]:
                return 0, 1
            elif scores[0][1] < scores[1][1]:
                return 1, 0
            else:
                return 2, 2 # they have the same hand