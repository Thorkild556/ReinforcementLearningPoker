import math
import numpy as np
import random

class Strategy():
    def __init__(self, n, gamma, alpha = 0.5, decay_rate = 0.05, epsilon = 0.1):
        self.n = n
        self.gamma = gamma
        self.alpha = alpha
        self.decay_rate = decay_rate
        self.epsilon = epsilon

        self.n_action_updates = [np.zeros([2, math.comb(11,2)*math.comb(9+i,0+i)]) for i in range(4)]  #generate the amount of unique states we have for having each amount of cards
        # given the 2 cards you have on your hand (11 chose 2), we have from 9 chose 0 to 12 chose 3 possible states since order doesnt matter.
        self.action_values =  [np.zeros([2, math.comb(11,2)*math.comb(9+i,0+i)]) for i in range(4)] 

    def _get_n_step_tree_backup(self, rewards: list[int], state_idxs: list[int], state_list_idxs: list[int], action_list: list[int], gamma, n, t):
        """
        This is for calculating the G_(t:t+n) given the recursive n_step_tree_back algorithm based on expected SARSA
        ##Params:
        takes in a full list respectively for each of all the rewards, states indeces, which state list (one for each amount of cards + terminal)
        """
        # we use t+1 because we want the expectation for the next state (not the one where we chose the action)
        state_list_idx = state_list_idxs[t+1] 
        reward = rewards[t]

        if state_list_idx == 4: #terminal state
            return reward
        
        state_idx = state_idxs[t+1]
        action = action_list[t]

        action_probas = self._get_action_probas_from_idx(state_list_idx, state_idx)
        action_vals = self.action_values[state_list_idx][:, state_idx]
        state_value = action_probas @ action_vals
        
        if n == 1:
            return reward + gamma*(state_value)
        
        not_action_value = state_value - action_probas[action] * action_vals[action]

        return reward + gamma * not_action_value + gamma * action_probas[action] * self._get_n_step_tree_backup(
                                                                                                                rewards, 
                                                                                                                state_idxs,
                                                                                                                state_list_idxs,
                                                                                                                action_list,
                                                                                                                gamma,
                                                                                                                n-1,
                                                                                                                t+1
                                                                                                                )

    def _get_action_proba_from_idx(self, state_list_idx, action, state_idx):
        action_values = self.action_values[state_list_idx][:, state_idx]
        argmax = np.argmax(action_values)
        return (1 - self.epsilon + self.epsilon/2) if action == argmax else self.epsilon/2

        
    def _get_action_probas_from_idx(self, state_list_idx, state_idx):
        probas = np.full(2, self.epsilon/2)
        argmax = np.argmax(self.action_values[state_list_idx][:, state_idx])
        probas[argmax] += 1-self.epsilon
        return probas


    def make_value_update(self, rewards: list[int], state_idxs: list[int], state_list_idxs: list[int], action_list: list[int], t, n):
        Gt = self._get_n_step_tree_backup(rewards, state_idxs, state_list_idxs, action_list, self.gamma, n, t)
        state_idx = state_idxs[t]
        state_list_idx = state_list_idxs[t]
        action = action_list[t]
        #getting alpha using the decay update rule: alpha = alpha_start / (1 + decay_rate * n_updates)
        alpha = self.alpha/(1 + self.decay_rate * self.n_action_updates[state_list_idx][action][state_idx]) 
        self.n_action_updates[state_list_idx][action][state_idx] += 1 # number of updates to that action goes up
        #using the update rule
        self.action_values[state_list_idx][action][state_idx] = self.action_values[state_list_idx][action][state_idx] + alpha*(Gt - self.action_values[state_list_idx][action][state_idx])
    
    def chose_action(self, board, hand):
        if np.random.random() < self.epsilon: # random
            return np.random.choice(2)
        else: # greedy
            return np.argmax(self._get_action_values(hand, board))

    def _get_action_values(self, cards, board):
        values = []
        for action in range(2):
            state = self._get_state_idx(cards, board)
            values.append(self.action_values[len(board)][action][state])
        return values
    
    def _get_action_probas(self, cards, board):
        probas = []
        for action in range(2):
            state = self._get_state_idx(cards, board)
            probas.append(self.action_probas[len(board)][action][state])
        return probas
    
    def _get_state_idx(self, hand, board):
        hand_idx = self._cards_to_index(hand, n=10)
        
        if len(board) == 0:
            return hand_idx
        
        board_idx = self._cards_to_index(board, n=10)
        
        # Number of possible board combinations
        n_board_combos = math.comb(10 + len(board) - 1, len(board))
        
        return hand_idx * n_board_combos + board_idx

    def _cards_to_index(self, cards, n = 10): #takes the cards and transforms into an index in a single list
        cards = sorted(cards)
        k = len(cards)
        rank = 0
        start = 1
        for i in range(k):
            for j in range(start, cards[i]):
                rank += math.comb(n - j + k - i - 1, k - i - 1)
            start = cards[i]
        return rank
    
    def _index_to_hand(self, index, k, n=10): #takes an index and transforms it into the corresponding hand
        """
        ##Params:
        index: the number to be converted back
        k: the number of cards to be converted 
        """
        combo = []
        start = 1
        for i in range(k):
            for val in range(start, n + 1):
                count = math.comb(n - val + k - i - 1, k - i - 1)
                if index < count:
                    combo.append(val)
                    start = val
                    break
                index -= count
        return combo