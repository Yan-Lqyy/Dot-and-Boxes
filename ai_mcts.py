# ai_mcts.py
"""Implementation of the Monte Carlo Tree Search (MCTS) policy."""
import random
import copy
import math
import time
import game_logic
from ai_helpers import get_all_valid_moves

MCTS_ITERATIONS = 1000
MCTS_EXPLORATION = 1.414

# --- MCTS Node (Unchanged) ---
class MCTSNode:
    # ... (implementation as before) ...
    def __init__(self, game_state, parent=None, move=None):
        self.game_state = game_state; self.parent = parent; self.move = move
        self.children = []; self.wins = 0.0; self.visits = 0
        self.untried_moves = get_all_valid_moves(self.game_state)
        self.player_just_moved = parent.game_state['current_player'] if parent else 3 - game_state['current_player']
    def uct_select_child(self, exploration_value=MCTS_EXPLORATION):
        if self.visits == 0: return None
        log_parent_visits = math.log(self.visits)
        def uct_score(child):
            if child.visits == 0: return float('inf')
            return (child.wins / child.visits) + exploration_value * math.sqrt(log_parent_visits / child.visits)
        return max(self.children, key=uct_score)
    def add_child(self, move, child_state):
        child = MCTSNode(game_state=child_state, parent=self, move=move)
        self.children.append(child)
        if move in self.untried_moves: self.untried_moves.remove(move)
        return child
    def update(self, result_winner):
        self.visits += 1
        player_to_move = self.game_state['current_player']
        if result_winner == player_to_move: self.wins += 1.0
        elif result_winner == 0: self.wins += 0.5
    def is_fully_expanded(self): return len(self.untried_moves) == 0
    def is_terminal(self): return game_logic.is_game_over(self.game_state)

# --- MCTS Simulation (Unchanged) ---
def mcts_simulate_random_game(start_state):
    # ... (implementation as before) ...
    current_state = copy.deepcopy(start_state); move_count = 0
    max_moves = (current_state['board_rows'] * (current_state['board_cols']-1) + current_state['board_cols'] * (current_state['board_rows']-1)) + 5
    while not game_logic.is_game_over(current_state):
        move_count += 1;
        if move_count > max_moves: print("Warning: MCTS sim exceeded max moves."); break
        valid_moves = get_all_valid_moves(current_state)
        if not valid_moves: break
        move = random.choice(valid_moves)
        boxes_completed = game_logic.make_move(current_state, move[0], move[1], move[2])
        if boxes_completed == 0: game_logic.switch_player(current_state)
    return game_logic.get_winner(current_state)

# --- MCTS Policy Entry Point (Track stop reason) ---
def get_mcts_move(game_state, iterations=MCTS_ITERATIONS, time_limit=None):
    """Policy entry point: Uses Monte Carlo Tree Search."""
    start_time = time.monotonic()

    if game_logic.is_game_over(game_state): return {'move': None, 'stop_reason': 'Game Over'}
    initial_valid_moves = get_all_valid_moves(game_state)
    if not initial_valid_moves: return {'move': None, 'stop_reason': 'No Valid Moves'}

    root = MCTSNode(game_state=copy.deepcopy(game_state))

    use_time_limit = time_limit is not None and time_limit > 0
    loop_count = 0
    max_loops = iterations if not use_time_limit else float('inf')
    time_limit_hit = False # Flag to track if time was the stop reason

    while loop_count < max_loops:
        loop_count += 1
        if use_time_limit and time.monotonic() - start_time > time_limit:
            time_limit_hit = True
            break

        # --- MCTS Phases ---
        node = root
        # 1. Selection
        while node.is_fully_expanded() and not node.is_terminal():
            node = node.uct_select_child()
            if node is None: break # Safety break
        # 2. Expansion
        if node and not node.is_terminal() and not node.is_fully_expanded():
            move = random.choice(node.untried_moves)
            next_state = copy.deepcopy(node.game_state)
            boxes_completed = game_logic.make_move(next_state, move[0], move[1], move[2])
            if boxes_completed == 0: game_logic.switch_player(next_state)
            node = node.add_child(move, next_state)
        # 3. Simulation
        simulation_result = mcts_simulate_random_game(node.game_state if node else root.game_state)
        # 4. Backpropagation
        temp_node = node if node else root
        while temp_node is not None:
            temp_node.update(simulation_result)
            temp_node = temp_node.parent
        # --- End MCTS Cycle ---

    # Determine stop reason
    stop_reason = "Unknown"
    if time_limit_hit:
        stop_reason = f"Time Limit Reached ({loop_count-1} iterations)"
    elif loop_count >= max_loops and not use_time_limit : # Check if iteration limit was the cause
        stop_reason = f"Iteration Limit Reached ({iterations} iterations)"
    else: # If neither limit hit explicitly, implies completed somehow (e.g., only one move)
         stop_reason = f"Completed ({loop_count-1} iterations)" # Default reason if no limit hit


    # --- Choose the best move ---
    best_move = None
    if not root.children:
         best_move = random.choice(initial_valid_moves) if initial_valid_moves else None
         stop_reason = "Fallback (No Children Explored)" # Override reason
         if best_move is None: stop_reason = 'No Valid Moves'
    else:
        # Choose child with highest visit count
        best_child = max(root.children, key=lambda c: c.visits)
        best_move = best_child.move

    return {'move': best_move, 'stop_reason': stop_reason}