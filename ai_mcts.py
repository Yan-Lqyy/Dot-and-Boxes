# ai_mcts.py
"""Implementation of the Monte Carlo Tree Search (MCTS) policy for Dots and Boxes."""
import random
import copy
import math
import time
import game_logic  # Assuming this module exists and has the specified functions
from ai_helpers import get_all_valid_moves # Assuming this helper exists

# --- MCTS Configuration ---
MCTS_ITERATIONS = 1000  # Default number of iterations if no time limit
MCTS_EXPLORATION = 1.414 # Exploration constant (sqrt(2)), balances exploration/exploitation

# --- MCTS Node ---
class MCTSNode:
    """
    Represents a node in the Monte Carlo Search Tree.
    Stores game state, win/visit counts, parent/children, and untried moves.
    """
    def __init__(self, game_state, parent=None, move=None):
        """
        Initializes a new MCTS node.

        Args:
            game_state (dict): The game state this node represents.
            parent (MCTSNode, optional): The parent node. Defaults to None (for root).
            move (tuple, optional): The move that led to this state from the parent. Defaults to None.
        """
        self.game_state = game_state  # The state of the game at this node
        self.parent = parent        # The node from which this node was reached
        self.move = move            # The move (line coordinates) that led to this state

        self.children = []          # List of child nodes
        self.wins = 0.0             # Number of simulations won from this node onwards (perspective of player who moved here)
        self.visits = 0             # Number of times this node has been visited during MCTS

        # Determine available moves from this state that haven't led to child nodes yet
        self.untried_moves = get_all_valid_moves(self.game_state)
        random.shuffle(self.untried_moves) # Shuffle for randomness in expansion

        # Determine which player made the move to arrive at this node's state.
        # If root node (no parent), it's the player opposite to the current player in the initial state.
        # Otherwise, it's the player who was 'current_player' in the parent's state.
        self.player_just_moved = parent.game_state['current_player'] if parent else (3 - game_state['current_player'])

    def uct_select_child(self, exploration_value=MCTS_EXPLORATION):
        """
        Selects a child node using the UCT (Upper Confidence Bound 1 applied to Trees) formula.
        Balances exploitation (choosing nodes with high win rates) and exploration (choosing less visited nodes).

        Args:
            exploration_value (float): The exploration constant (C in the UCT formula).

        Returns:
            MCTSNode: The child node with the highest UCT score, or None if this node has no visits/children yet.
        """
        # If a node hasn't been visited, its UCT score is effectively infinite, but selection only happens on visited nodes.
        # This check prevents division by zero if called inappropriately, though standard MCTS avoids this.
        if self.visits == 0:
             return None

        # Pre-calculate log of parent visits for efficiency
        log_parent_visits = math.log(self.visits)

        def uct_score(child):
            """Calculates the UCT score for a given child node."""
            if child.visits == 0:
                # Assign infinite score to unvisited children to ensure they are selected first
                return float('inf')
            # UCT formula: (Average Wins) + C * sqrt(log(Parent Visits) / Child Visits)
            average_wins = child.wins / child.visits
            exploration_term = exploration_value * math.sqrt(log_parent_visits / child.visits)
            return average_wins + exploration_term

        # Return the child with the maximum UCT score
        return max(self.children, key=uct_score)

    def add_child(self, move, child_state):
        """
        Adds a new child node to this node.

        Args:
            move (tuple): The move that leads to the child state.
            child_state (dict): The game state of the child node.

        Returns:
            MCTSNode: The newly created child node.
        """
        # Create the child node, linking it back to this node (as parent)
        child = MCTSNode(game_state=child_state, parent=self, move=move)
        self.children.append(child)

        # Remove the move that led to this child from the list of untried moves
        # Use a loop for safe removal in case the move tuple format needs exact matching
        for i, untried_move in enumerate(self.untried_moves):
             if untried_move == move:
                 self.untried_moves.pop(i)
                 break
        return child

    def update(self, result_winner):
        """
        Updates the win/visit counts for this node based on a simulation result.
        Scores are updated from the perspective of the player who moved TO this node.

        Args:
            result_winner (int): The player who won the simulation (1 or 2), or 0 for a draw.
        """
        self.visits += 1

        # *** CORRECTED LOGIC ***
        # We update the score based on whether the player who *moved to this state*
        # (self.player_just_moved) won the simulation.
        if result_winner == self.player_just_moved:
            self.wins += 1.0  # Increment wins if the player who moved here won
        elif result_winner == 0:
            self.wins += 0.5  # Increment by 0.5 for a draw
        # Else (the opponent won), wins are implicitly incremented by 0.0 (no change)

    def is_fully_expanded(self):
        """Checks if all possible moves from this node's state have been explored (have corresponding children)."""
        return len(self.untried_moves) == 0

    def is_terminal(self):
        """Checks if the game state represented by this node is a terminal state (game over)."""
        return game_logic.is_game_over(self.game_state)

# --- MCTS Simulation (Random Playout) ---
def mcts_simulate_random_game(start_state):
    """
    Simulates a game from the start_state using random moves until a terminal state is reached.
    This is the 'Simulation' or 'Rollout' phase of MCTS.

    Args:
        start_state (dict): The game state from which to start the simulation.

    Returns:
        int: The winner of the simulated game (1 or 2), or 0 for a draw.
    """
    current_state = copy.deepcopy(start_state) # Work on a copy
    move_count = 0
    # Estimate max possible moves to prevent infinite loops in rare cases
    max_moves_estimate = (current_state['board_rows'] * (current_state['board_cols'] + 1) +
                         current_state['board_cols'] * (current_state['board_rows'] + 1)) + 10 # Generous buffer

    while not game_logic.is_game_over(current_state):
        move_count += 1
        if move_count > max_moves_estimate:
            print(f"Warning: MCTS simulation exceeded max moves ({max_moves_estimate}). State: {current_state}")
            # If stuck, might indicate an issue in game logic or simulation; return draw as fallback
            return 0

        valid_moves = get_all_valid_moves(current_state)
        if not valid_moves:
            # Should not happen if is_game_over is correct, but handle defensively
            break

        # Choose a random valid move
        move = random.choice(valid_moves)

        # Apply the move
        boxes_completed = game_logic.make_move(current_state, move[0], move[1], move[2])

        # Switch player only if no box was completed (Dots and Boxes rule)
        if boxes_completed == 0:
            game_logic.switch_player(current_state)

    # Once the game is over, determine the winner
    return game_logic.get_winner(current_state)

# --- MCTS Policy Entry Point ---
def get_mcts_move(game_state, iterations=MCTS_ITERATIONS, time_limit=None):
    """
    Determines the best move from the current game state using MCTS.

    Args:
        game_state (dict): The current state of the game.
        iterations (int): The number of MCTS iterations to run (if no time_limit).
        time_limit (float, optional): The maximum time in seconds to run MCTS. Overrides iterations if set.

    Returns:
        dict: A dictionary containing:
            'move' (tuple or None): The best move found, or None if no move is possible/game over.
            'stop_reason' (str): Explanation of why the search stopped (iteration limit, time limit, etc.).
    """
    start_time = time.monotonic()

    # Handle edge cases where no move is possible or needed
    if game_logic.is_game_over(game_state):
        return {'move': None, 'stop_reason': 'Game Over'}
    initial_valid_moves = get_all_valid_moves(game_state)
    if not initial_valid_moves:
        return {'move': None, 'stop_reason': 'No Valid Moves'}
    # If only one move is possible, return it immediately
    if len(initial_valid_moves) == 1:
         return {'move': initial_valid_moves[0], 'stop_reason': 'Only One Move Available'}

    # Create the root node of the search tree
    root = MCTSNode(game_state=copy.deepcopy(game_state))

    # Determine stopping condition: time limit or iteration count
    use_time_limit = time_limit is not None and time_limit > 0
    loop_count = 0
    # Set a very large number for iterations if using time limit, effectively making time the only constraint
    max_loops = iterations if not use_time_limit else float('inf')
    time_limit_hit = False # Flag to track if time was the stop reason

    # --- Main MCTS Loop ---
    while loop_count < max_loops:
        loop_count += 1

        # Check for time limit stop condition
        if use_time_limit and time.monotonic() - start_time >= time_limit:
            time_limit_hit = True
            break # Exit loop if time limit reached

        # --- MCTS Phases ---
        node = root # Start traversal from the root

        # 1. Selection: Traverse the tree using UCT until a leaf node or non-fully expanded node is found
        while node.is_fully_expanded() and not node.is_terminal():
            selected_node = node.uct_select_child()
            if selected_node is None:
                # This might happen if root has visits but no children yet expanded (should be rare with proper loop)
                # Or if a node somehow has visits but no children added. Break defensively.
                print("Warning: uct_select_child returned None during selection.")
                break
            node = selected_node
        # If selection ended prematurely (e.g., warning above), use the last valid node
        if node is None: node = root # Fallback safely


        # 2. Expansion: If the selected node is not terminal and not fully expanded, add a new child node
        if not node.is_terminal() and not node.is_fully_expanded():
            # Choose an untried move randomly
            move = node.untried_moves[0] # Pop removes & returns; already shuffled in __init__
            # Create the state resulting from this move
            next_state = copy.deepcopy(node.game_state)
            boxes_completed = game_logic.make_move(next_state, move[0], move[1], move[2])
            # Handle player switching based on Dots and Boxes rules
            if boxes_completed == 0:
                game_logic.switch_player(next_state)
            # Add the new child node to the tree and advance to it for simulation
            node = node.add_child(move, next_state)

        # 3. Simulation (Rollout): Simulate a random game from the newly expanded node (or selected terminal/leaf node)
        # If expansion happened, 'node' is the new child. If selection hit a terminal or fully expanded node, 'node' is that node.
        simulation_result = mcts_simulate_random_game(node.game_state)

        # 4. Backpropagation: Update win/visit counts back up the tree from the simulated node to the root
        temp_node = node
        while temp_node is not None:
            temp_node.update(simulation_result) # Use the corrected update method
            temp_node = temp_node.parent # Move up to the parent
        # --- End of MCTS Cycle ---

    # --- Determine Stop Reason ---
    stop_reason = "Unknown"
    actual_iterations = loop_count - 1 if time_limit_hit else loop_count # Adjust count if loop broke early

    if time_limit_hit:
        stop_reason = f"Time Limit Reached ({time_limit:.2f}s, {actual_iterations} iterations)"
    elif loop_count >= max_loops and not use_time_limit: # Check if iteration limit was the cause
        stop_reason = f"Iteration Limit Reached ({iterations} iterations)"
    else: # If neither limit hit explicitly (e.g., maybe tree fully explored quickly?)
         stop_reason = f"Completed ({actual_iterations} iterations)"

    # --- Choose the Best Move ---
    best_move = None
    if not root.children:
         # Should only happen if 0 iterations were run or initial state had few options
         # Fallback to a random move if no children were explored
         best_move = random.choice(initial_valid_moves) if initial_valid_moves else None
         if not best_move and not game_logic.is_game_over(game_state):
             # This case indicates an issue, possibly no valid moves from start
              stop_reason = "Fallback Failed (No Children/No Valid Moves)"
         elif best_move:
              stop_reason = f"Fallback (No Children Explored, {actual_iterations} iterations)"

    else:
        # Standard MCTS: Choose the child node that was visited the most times
        # This is considered the most robust move ("Robust Child" policy)
        best_child = max(root.children, key=lambda c: c.visits)
        best_move = best_child.move
        # Add stats to stop reason for clarity
        best_child_stats = f"Visits={best_child.visits}, WinRate={best_child.wins/best_child.visits:.2f}" if best_child.visits > 0 else "Visits=0"
        stop_reason += f" | Best Move Stats: {best_child_stats}"


    return {'move': best_move, 'stop_reason': stop_reason}
