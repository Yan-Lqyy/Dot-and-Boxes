# ai_mcts.py
"""
Implementation of the Monte Carlo Tree Search (MCTS) policy.
"""
import random
import copy
import math
import time
import game_logic

# Import necessary helpers
from ai_helpers import get_all_valid_moves # Primarily for MCTSNode initialization and simulation fallback

# --- Constants specific to MCTS ---
MCTS_ITERATIONS = 1000   # Default iterations if time limit not used
MCTS_EXPLORATION = 1.414 # Exploration factor (sqrt(2))

# --- MCTS Node ---
class MCTSNode:
    """Node in the MCTS tree."""
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state # The state represented by this node
        self.parent = parent       # Parent node
        self.move = move           # Move that led to this node from parent
        self.children = []         # Child nodes
        self.wins = 0.0            # Use float for potential 0.5 wins from ties
        self.visits = 0            # Number of visits to this node
        self.untried_moves = get_all_valid_moves(self.game_state)
        # Player who just moved to reach this state. If root, opponent of current player.
        self.player_just_moved = parent.game_state['current_player'] if parent else 3 - game_state['current_player']

    def uct_select_child(self, exploration_value=MCTS_EXPLORATION):
        """Selects a child node using the UCB1 formula."""
        if self.visits == 0: return None # Safety check

        log_parent_visits = math.log(self.visits)

        def uct_score(child):
            if child.visits == 0:
                return float('inf') # Explore unvisited children first
            win_rate = child.wins / child.visits
            exploration = exploration_value * math.sqrt(log_parent_visits / child.visits)
            # print(f"  Child {child.move}: WR={win_rate:.2f}, Exp={exploration:.2f}, Score={win_rate + exploration:.2f}, V={child.visits}, W={child.wins}")
            return win_rate + exploration

        selected_child = max(self.children, key=uct_score)
        return selected_child

    def add_child(self, move, child_state):
        """Adds a new child node."""
        child = MCTSNode(game_state=child_state, parent=self, move=move)
        self.children.append(child)
        # Remove move from *parent's* untried list
        if move in self.untried_moves:
             self.untried_moves.remove(move)
        return child

    def update(self, result_winner):
        """Updates node statistics. result_winner is 1, 2, or 0."""
        self.visits += 1
        # Determine if the player *to move* from this node's state won
        player_to_move = self.game_state['current_player']
        if result_winner == player_to_move:
            self.wins += 1.0
        elif result_winner == 0: # Tie
            self.wins += 0.5
        # else: player_just_moved won, or opponent won, so wins for player_to_move is 0

    def is_fully_expanded(self):
        return len(self.untried_moves) == 0

    def is_terminal(self):
        return game_logic.is_game_over(self.game_state)

# --- MCTS Simulation ---
def mcts_simulate_random_game(start_state):
    """Simulates a random game from start_state. Returns winner (1, 2, or 0)."""
    current_state = copy.deepcopy(start_state)
    move_count = 0 # Add a safety break for potential infinite loops
    max_moves = (current_state['board_rows'] * (current_state['board_cols']-1) +
                 current_state['board_cols'] * (current_state['board_rows']-1)) + 5 # Max possible lines + buffer

    while not game_logic.is_game_over(current_state):
        move_count += 1
        if move_count > max_moves:
             print("Warning: MCTS simulation exceeded max moves. Breaking.")
             break # Safety break

        valid_moves = get_all_valid_moves(current_state)
        if not valid_moves:
            break

        move = random.choice(valid_moves)
        boxes_completed = game_logic.make_move(current_state, move[0], move[1], move[2])

        if boxes_completed == 0:
            game_logic.switch_player(current_state)

    return game_logic.get_winner(current_state)

# --- MCTS Policy Entry Point ---
def get_mcts_move(game_state, iterations=MCTS_ITERATIONS, time_limit=None):
    """Policy entry point: Uses Monte Carlo Tree Search."""
    start_time = time.monotonic()

    # Check initial state
    if game_logic.is_game_over(game_state): return None
    initial_valid_moves = get_all_valid_moves(game_state)
    if not initial_valid_moves: return None

    root = MCTSNode(game_state=copy.deepcopy(game_state))

    # Determine loop condition
    use_time_limit = time_limit is not None and time_limit > 0
    loop_count = 0
    max_loops = iterations if not use_time_limit else float('inf')

    while loop_count < max_loops:
        loop_count += 1
        if use_time_limit and time.monotonic() - start_time > time_limit:
            # print(f" MCTS time limit reached after {loop_count-1} iterations.")
            break

        # --- MCTS Phases ---
        node = root

        # 1. Selection
        while node.is_fully_expanded() and not node.is_terminal():
            node = node.uct_select_child()
            if node is None: # Should not happen if fully expanded but not terminal
                 print("Warning: MCTS selection failed unexpectedly.")
                 node = root # Reset to root? Or handle error
                 break

        # 2. Expansion
        if not node.is_terminal() and not node.is_fully_expanded():
            move = random.choice(node.untried_moves)
            next_state = copy.deepcopy(node.game_state)
            boxes_completed = game_logic.make_move(next_state, move[0], move[1], move[2])
            if boxes_completed == 0:
                 game_logic.switch_player(next_state)
            node = node.add_child(move, next_state) # node becomes the newly added child

        # 3. Simulation
        # Ensure node is not None if selection failed above
        if node:
             simulation_result = mcts_simulate_random_game(node.game_state)
        else:
             simulation_result = mcts_simulate_random_game(root.game_state) # Simulate from root if selection failed


        # 4. Backpropagation
        temp_node = node if node else root # Start backprop from where simulation started
        while temp_node is not None:
            temp_node.update(simulation_result)
            temp_node = temp_node.parent
        # --- End MCTS Cycle ---

    # --- Choose the best move ---
    if not root.children:
         # print("Warning: MCTS finished with no children explored. Choosing random move.")
         return random.choice(initial_valid_moves) if initial_valid_moves else None

    # Choose child with highest visit count (most robust)
    best_child = max(root.children, key=lambda c: c.visits)

    # Debug info (optional)
    # print(f" MCTS ran {loop_count-1} iterations in {time.monotonic() - start_time:.3f}s")
    # for child in sorted(root.children, key=lambda c: c.visits, reverse=True):
    #     print(f"  - Mv {child.move}: V={child.visits}, W={child.wins:.1f}, WR={child.wins/child.visits if child.visits else 0:.3f}")

    return best_child.move