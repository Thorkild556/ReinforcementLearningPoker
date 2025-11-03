import dearpygui.dearpygui as dpg
from src.game import RLPlayer, HumanPlayer
from src.strategy import Strategy
import numpy as np
import pickle

def draw_cards(deck, n):
    indices = np.random.choice(len(deck), size=n, replace=False)
    indices = sorted(indices, reverse=True)
    cards = [deck[idx] for idx in indices]
    for card in indices:
        del deck[card]
    return cards

def get_unique(hand):
    return np.unique(hand, return_counts=True)

def get_hand_description(hand):
    """Get a description of the best hand combination"""
    unique_vals, counts = get_unique(hand)
    max_count = np.max(counts)
    argmx = np.where(counts == max_count)[0][-1]
    best_card = unique_vals[argmx]
    
    if max_count == 4:
        return f"Four of a kind: {best_card}'s"
    elif max_count == 3:
        return f"Three of a kind: {best_card}'s"
    elif max_count == 2:
        return f"Pair of {best_card}'s"
    else:
        return f"High card: {best_card}"

def get_winner(hands):
    unique_hands = [get_unique(hand) for hand in hands]
    scores = [[], []]
    for i, hand in enumerate(unique_hands):
        max_uniq = np.max(hand[1])
        argmx = np.where(hand[1] == hand[1].max())[0][-1]
        max_value = hand[0][argmx]
        scores[i].extend([max_uniq, max_value])
    if scores[0][0] > scores[1][0]:
        return 0, 1
    elif scores[0][0] < scores[1][0]:
        return 1, 0
    else:
        if scores[0][1] > scores[1][1]:
            return 0, 1
        elif scores[0][1] < scores[1][1]:
            return 1, 0
        else:
            return 2, 2

# Game state
class GameState:
    def __init__(self):
        with open("strat/strat.pkl", "rb") as f:
            strat = pickle.load(f)
        self.rlplayer = RLPlayer(strat)
        self.rlplayer.credits = 30
        self.human_player = HumanPlayer()
        self.human_player.credits = 30
        self.stake = 1
        self.deck = []
        self.board = []
        self.t = 0
        self.end = False
        self.game_active = False
        self.game_over = False
        self.last_showdown_info = ""
        self.game_started = False
        
    def new_game(self):
        self.stake = 1
        self.deck = [j for j in range(1, 11) for _ in range(4)]
        self.board = []
        self.rlplayer.new_hand(draw_cards(self.deck, 2))
        self.human_player.new_hand(draw_cards(self.deck, 2))
        self.t = 0
        self.end = False
        self.game_active = True
        self.game_over = False
        self.last_showdown_info = ""
        self.update_display()
        
    def update_display(self):
        dpg.set_value("human_credits", f"{self.human_player.credits}")
        dpg.set_value("rl_credits", f"{self.rlplayer.credits}")
        dpg.set_value("human_hand", f"{self.human_player.hand}")
        
        if self.end or not self.game_active:
            dpg.set_value("rl_hand", f"{self.rlplayer.hand}")
        else:
            dpg.set_value("rl_hand", "? ?")
        
        dpg.set_value("board", f"{self.board}" if self.board else "Empty")
        
        # Show/hide stake based on game state
        if self.end or not self.game_active:
            dpg.configure_item("stake_group", show=False)
        else:
            dpg.configure_item("stake_group", show=True)
            dpg.set_value("stake", f"{self.stake}")
            dpg.set_value("stake_info", f"Next stake: {self.stake*2}")
        
        # Update showdown info display
        if self.last_showdown_info:
            dpg.set_value("showdown_info", self.last_showdown_info)
            dpg.configure_item("showdown_section", show=True)
        else:
            dpg.configure_item("showdown_section", show=False)
        
        # Check for game over
        if self.human_player.credits <= 0:
            self.game_over = True
            dpg.configure_item("game_over_window", show=True)
            dpg.set_value("game_over_title", "GAME OVER")
            dpg.set_value("game_over_message", "You are out of credits!\nRLPlayer wins the match!")
            dpg.configure_item("main_content", show=False)
        elif self.rlplayer.credits <= 0:
            self.game_over = True
            dpg.configure_item("game_over_window", show=True)
            dpg.set_value("game_over_title", "VICTORY!")
            dpg.set_value("game_over_message", "RLPlayer is out of credits!\nYou win the match!")
            dpg.configure_item("main_content", show=False)
        else:
            dpg.configure_item("game_over_window", show=False)
            dpg.configure_item("main_content", show=True)
            
            if self.end:
                dpg.set_value("message", "Hand complete")
                # Change buttons to New Hand and Quit
                dpg.set_item_label("call_btn", "New Hand")
                dpg.set_item_label("fold_btn", "Quit")
                dpg.configure_item("call_btn", enabled=True)
                dpg.configure_item("fold_btn", enabled=True)
            else:
                dpg.set_value("message", "Your turn - Call or Fold?")
                # Restore buttons to CALL and FOLD
                dpg.set_item_label("call_btn", "CALL")
                dpg.set_item_label("fold_btn", "FOLD")
                dpg.configure_item("call_btn", enabled=True)
                dpg.configure_item("fold_btn", enabled=True)
    
    def process_action(self, human_action):
        if not self.game_active or self.end:
            return
            
        rl_action = self.rlplayer.take_action(self.board)
        
        result_message = f"RLPlayer: {'CALL' if rl_action==0 else 'FOLD'}\n"
        result_message += f"You: {'CALL' if human_action==0 else 'FOLD'}\n\n"
        
        # Reset showdown info for non-showdown rounds
        self.last_showdown_info = ""
        
        if rl_action == 0 and human_action == 0:
            if self.t != 3:
                result_message += "Both called - continuing to next round\n"
                self.end = False
            else:
                self.end = False  # Will handle showdown below
        elif rl_action == 1 and human_action == 1:
            result_message += "Both folded - no credits exchanged\n"
            self.end = True
        else:
            for idx in range(2):
                if [rl_action, human_action][idx] == 0:
                    reward = self.stake
                else:
                    reward = -self.stake
                if idx == 1:
                    self.human_player.credits += reward
                    result_message += f"{'You WON' if reward>0 else 'You LOST'} {abs(reward)} credits\n"
                if idx == 0:
                    self.rlplayer.credits += reward
                    result_message += f"{'RLPlayer WON' if reward>0 else 'RLPlayer LOST'} {abs(reward)} credits\n"
            self.end = True
        
        # Handle showdown at t=3 if both called
        if self.t == 3 and not self.end:
            hand0 = self.rlplayer.hand + self.board
            hand1 = self.human_player.hand + self.board
            winner, loser = get_winner([hand0, hand1])
            
            # Create detailed showdown information
            rl_combo = get_hand_description(hand0)
            human_combo = get_hand_description(hand1)
            
            self.last_showdown_info = f"YOUR HAND: {self.human_player.hand} + BOARD: {self.board}\n"
            self.last_showdown_info += f"Your best: {human_combo}\n\n"
            self.last_showdown_info += f"RLPLAYER HAND: {self.rlplayer.hand} + BOARD: {self.board}\n"
            self.last_showdown_info += f"RLPlayer best: {rl_combo}\n\n"
            
            if winner != 2:
                if winner == 1:
                    self.human_player.credits += self.stake * 2
                    self.rlplayer.credits -= self.stake * 2
                    result_message += f"SHOWDOWN: You WIN! +{self.stake*2} credits\n"
                    result_message += f"RLPlayer loses {self.stake*2} credits\n"
                    self.last_showdown_info += ">>> YOU WIN THE SHOWDOWN!"
                else:
                    self.human_player.credits -= self.stake * 2
                    self.rlplayer.credits += self.stake * 2
                    result_message += f"SHOWDOWN: You LOSE! -{self.stake*2} credits\n"
                    result_message += f"RLPlayer wins {self.stake*2} credits\n"
                    self.last_showdown_info += ">>> RLPLAYER WINS THE SHOWDOWN!"
            else:
                result_message += "SHOWDOWN: It's a TIE!\n"
                self.last_showdown_info += ">>> IT'S A TIE!"
            self.end = True
        
        if not self.end:
            self.board.extend(draw_cards(self.deck, 1))
            result_message += f"\nNew card dealt: {self.board[-1]}\n"
            self.t += 1
            self.stake *= 2
        
        dpg.set_value("result", result_message)
        self.update_display()

game_state = GameState()

def action_button_callback():
    """Handles both CALL and New Hand actions"""
    if game_state.end:
        # Button is "New Hand" - start new hand
        dpg.set_value("result", "")
        game_state.new_game()
    else:
        # Button is "CALL" - process call action
        game_state.process_action(0)

def fold_quit_button_callback():
    """Handles both FOLD and Quit actions"""
    if game_state.end:
        # Button is "Quit" - quit the game
        dpg.stop_dearpygui()
    else:
        # Button is "FOLD" - process fold action
        game_state.process_action(1)

def new_match_callback():
    game_state.human_player.credits = 30
    game_state.rlplayer.credits = 30
    dpg.set_value("result", "")
    game_state.new_game()

def start_game_callback():
    dpg.configure_item("welcome_screen", show=False)
    dpg.configure_item("main_content", show=True)
    game_state.game_started = True
    game_state.new_game()

# Create DearPyGUI context
dpg.create_context()

# Create window with improved layout
with dpg.window(label="RL Poker", tag="main_window", width=900, height=950, no_scrollbar=True):
    # Welcome/Rules screen
    with dpg.group(tag="welcome_screen"):
        dpg.add_spacer(height=50)
        dpg.add_text("WELCOME TO RL POKER", tag="welcome_title")
        dpg.add_spacer(height=30)
        
        with dpg.child_window(width=860, height=600, border=True):
            dpg.add_spacer(height=20)
            dpg.add_text("GAME RULES")
            dpg.add_spacer(height=20)
            
            dpg.add_text("OBJECTIVE:", bullet=True)
            dpg.add_text("Win all of your opponent's credits. You both start with 30 credits.")
            dpg.add_spacer(height=10)
            
            dpg.add_text("GAMEPLAY:", bullet=True)
            dpg.add_text("- Each hand consists of up to 4 rounds of betting")
            dpg.add_text("- You receive 2 private cards, and community cards are revealed on the board")
            dpg.add_text("- Each round, you can CALL (continue) or FOLD (give up)")
            dpg.add_text("- Stakes double each round: 1 -> 2 -> 4 -> 8")
            dpg.add_spacer(height=10)
            
            dpg.add_text("WINNING A HAND:", bullet=True)
            dpg.add_text("- If one player folds, the other wins the current stake")
            dpg.add_text("- If both call all 4 rounds, there's a SHOWDOWN")
            dpg.add_text("- At showdown, the best hand wins double the final stake")
            dpg.add_spacer(height=10)
            
            dpg.add_text("HAND RANKINGS (Best to Worst):", bullet=True)
            dpg.add_text("1. Four of a Kind (e.g., 7-7-7-7)")
            dpg.add_text("2. Three of a Kind (e.g., 5-5-5)")
            dpg.add_text("3. Pair (e.g., 9-9)")
            dpg.add_text("4. High Card (highest single card)")
            dpg.add_spacer(height=10)
            
            dpg.add_text("ABOUT YOUR OPPONENT:", bullet=True)
            dpg.add_text("- RLPlayer is trained using Reinforcement Learning")
            dpg.add_text("- RLPlayer makes decisions based ONLY on the board cards")
            dpg.add_text("- RLPlayer has NO knowledge of your private cards")
            dpg.add_text("- RLPlayer learned strategy through self-play over many games")
            dpg.add_spacer(height=10)
            
            dpg.add_text("CARDS:", bullet=True)
            dpg.add_text("The deck contains cards numbered 1-10, with 4 of each number")
            dpg.add_spacer(height=20)
        
        dpg.add_spacer(height=30)
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=320)
            dpg.add_button(label="START GAME", callback=start_game_callback, width=250, height=70)
    
    # Title (hidden initially)
    dpg.add_text("RL POKER", tag="title")
    dpg.add_separator()
    
    # Main content group (hidden initially until game starts)
    with dpg.group(tag="main_content", show=False):
        # Main message
        dpg.add_text("Your turn - Call or Fold?", tag="message")
        dpg.add_spacer(height=10)
        
        # Credits section
        with dpg.group(horizontal=True):
            with dpg.child_window(width=420, height=80, border=True):
                dpg.add_text("YOUR CREDITS")
                dpg.add_spacer(height=5)
                dpg.add_text("30", tag="human_credits")
            
            dpg.add_spacer(width=20)
            
            with dpg.child_window(width=420, height=80, border=True):
                dpg.add_text("RLPLAYER CREDITS")
                dpg.add_spacer(height=5)
                dpg.add_text("30", tag="rl_credits")
        
        dpg.add_spacer(height=15)
        
        # Hands section - side by side for easy comparison
        with dpg.group(horizontal=True):
            with dpg.child_window(width=420, height=100, border=True):
                dpg.add_text("YOUR HAND")
                dpg.add_spacer(height=5)
                dpg.add_text("[]", tag="human_hand")
            
            dpg.add_spacer(width=20)
            
            with dpg.child_window(width=420, height=100, border=True):
                dpg.add_text("RLPLAYER HAND")
                dpg.add_spacer(height=5)
                dpg.add_text("? ?", tag="rl_hand")
        
        dpg.add_spacer(height=15)
        
        # Board section
        with dpg.child_window(width=860, height=90, border=True):
            dpg.add_text("BOARD (Community Cards)")
            dpg.add_spacer(height=5)
            dpg.add_text("Empty", tag="board")
        
        dpg.add_spacer(height=15)
        
        # Stake info (only visible during active play)
        with dpg.group(tag="stake_group", horizontal=True):
            with dpg.child_window(width=420, height=80, border=True):
                dpg.add_text("CURRENT STAKE")
                dpg.add_spacer(height=5)
                dpg.add_text("1", tag="stake")
            
            dpg.add_spacer(width=20)
            
            with dpg.child_window(width=420, height=80, border=True):
                dpg.add_text("IF YOU CALL")
                dpg.add_spacer(height=5)
                dpg.add_text("Next stake: 2", tag="stake_info")
        
        dpg.add_spacer(height=15)
        
        # Action buttons (dynamic labels: CALL/FOLD or New Hand/Quit)
        with dpg.group(horizontal=True):
            dpg.add_button(label="CALL", tag="call_btn", callback=action_button_callback, width=180, height=60)
            dpg.add_spacer(width=20)
            dpg.add_button(label="FOLD", tag="fold_btn", callback=fold_quit_button_callback, width=180, height=60)
        
        dpg.add_spacer(height=15)
        dpg.add_separator()
        
        # Showdown comparison section (only visible after showdown)
        with dpg.group(tag="showdown_section", show=False):
            dpg.add_text("SHOWDOWN COMPARISON")
            with dpg.child_window(width=860, height=110, border=True):
                dpg.add_text("", tag="showdown_info", wrap=840)
            dpg.add_spacer(height=10)
            dpg.add_separator()
        
        # Result area
        dpg.add_text("ROUND RESULT")
        dpg.add_text("", tag="result", wrap=840)
        
        dpg.add_spacer(height=15)
        dpg.add_separator()
        
        # Bottom quit button
        with dpg.group(horizontal=True):
            dpg.add_spacer(width=690)
            dpg.add_button(label="Quit Game", callback=lambda: dpg.stop_dearpygui(), width=150, height=50)
    
    # Game Over overlay (hidden by default)
    with dpg.child_window(tag="game_over_window", width=860, height=600, border=False, show=False, pos=[20, 75]):
        dpg.add_spacer(height=200)
        with dpg.child_window(width=800, height=300, border=True, pos=[30, 200]):
            dpg.add_spacer(height=40)
            dpg.add_text("GAME OVER", tag="game_over_title")
            dpg.add_spacer(height=20)
            dpg.add_text("Message here", tag="game_over_message", wrap=700)
            dpg.add_spacer(height=40)
            with dpg.group(horizontal=True):
                dpg.add_spacer(width=200)
                dpg.add_button(label="New Match", callback=new_match_callback, width=180, height=60)
                dpg.add_spacer(width=40)
                dpg.add_button(label="Quit", callback=lambda: dpg.stop_dearpygui(), width=180, height=60)

# Setup and start
dpg.create_viewport(title="RL Poker", width=950, height=1000)
dpg.setup_dearpygui()

# Set global font scale
dpg.set_global_font_scale(1.3)

dpg.show_viewport()
dpg.set_primary_window("main_window", True)

dpg.start_dearpygui()
dpg.destroy_context()