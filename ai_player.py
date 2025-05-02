# ai_player.py
"""
Contains different AI policies (strategies) for playing Dots and Boxes.
Each policy function takes the current game_state and returns a valid move (line_type, r, c).
"""

import random
import game_logic
import copy  # Needed for deep copying game state in search
import math  # For infinity

# Constants for search
DEFAULT_SEARCH_DEPTH = 3 # Adjust as needed for performance/strength trade-off

# --- Helper Functions ---

def _get_all_valid_moves(game_state):
    """Returns a list of all valid moves [(type, r, c), ...] currently available."""
    valid_moves = []
    rows = game_state['board_rows']
    cols = game_state['board_cols']

    # Check horizontal lines
    for r in range(rows):
        for c in range(cols - 1):
            if game_logic.is_valid_line(game_state, 'h', r, c):
                valid_moves.append(('h', r, c))

    # Check vertical lines
    for r in range(rows - 1):
        for c in range(cols):
            if game_logic.is_valid_line(game_state, 'v', r, c):
                valid_moves.append(('v', r, c))

    return valid_moves

def _count_box_sides(game_state, box_r, box_c):
    """Counts the number of existing sides for a box at (box_r, box_c)."""
    # Ensure box coordinates are valid before checking lines
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    if not (0 <= box_r < rows - 1 and 0 <= box_c < cols - 1):
        return 0 # Invalid box coordinates

    count = 0
    h_lines = game_state['horizontal_lines']
    v_lines = game_state['vertical_lines']

    # Top line
    if (box_r, box_c) in h_lines: count += 1
    # Bottom line
    if (box_r + 1, box_c) in h_lines: count += 1
    # Left line
    if (box_r, box_c) in v_lines: count += 1
    # Right line
    if (box_r, box_c + 1) in v_lines: count += 1

    return count

def _completes_box(game_state, line_type, r, c):
    """Checks if adding the line (line_type, r, c) would complete any box."""
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    temp_h_lines = game_state['horizontal_lines'].copy()
    temp_v_lines = game_state['vertical_lines'].copy()

    # Temporarily add the line
    if line_type == 'h':
        temp_h_lines.add((r, c))
    else:
        temp_v_lines.add((r, c))

    # Create a temporary state view for checking
    temp_state_view = {
        'horizontal_lines': temp_h_lines,
        'vertical_lines': temp_v_lines,
        'board_rows': rows,
        'board_cols': cols
    }

    # Check the box(es) adjacent to this line
    boxes_completed = 0
    if line_type == 'h':
        # Box below the line (r, c)
        if r < rows - 1:
            if _count_box_sides(temp_state_view, r, c) == 4: boxes_completed += 1
        # Box above the line (r-1, c)
        if r > 0:
             if _count_box_sides(temp_state_view, r - 1, c) == 4: boxes_completed += 1
    elif line_type == 'v':
        # Box to the right of the line (r, c)
        if c < cols - 1:
             if _count_box_sides(temp_state_view, r, c) == 4: boxes_completed += 1
        # Box to the left of the line (r, c-1)
        if c > 0:
             if _count_box_sides(temp_state_view, r, c - 1) == 4: boxes_completed += 1

    return boxes_completed > 0

def _adds_third_line(game_state, line_type, r, c):
    """
    Checks if adding the line (line_type, r, c) adds the 3rd side to any box
    (without completing it - that's handled by _completes_box).
    """
    rows = game_state['board_rows']
    cols = game_state['board_cols']

    # Check the box(es) adjacent to this line
    if line_type == 'h':
        # Box below the line (r, c)
        if r < rows - 1:
            if _count_box_sides(game_state, r, c) == 2: return True
        # Box above the line (r-1, c)
        if r > 0:
             if _count_box_sides(game_state, r - 1, c) == 2: return True
    elif line_type == 'v':
        # Box to the right of the line (r, c)
        if c < cols - 1:
             if _count_box_sides(game_state, r, c) == 2: return True
        # Box to the left of the line (r, c-1)
        if c > 0:
             if _count_box_sides(game_state, r, c - 1) == 2: return True

    return False

def _third_line_sacrifice_count(game_state, line_type, r, c):
    """
    Counts how many boxes this move adds the third line to.
    Used by Minimal Sacrifice policy when forced to give away points.
    Returns 0, 1, or 2.
    """
    count = 0
    rows = game_state['board_rows']
    cols = game_state['board_cols']

    # Check the box(es) adjacent to this line
    if line_type == 'h':
        if r < rows - 1 and _count_box_sides(game_state, r, c) == 2:
            count += 1
        if r > 0 and _count_box_sides(game_state, r - 1, c) == 2:
            count += 1
    elif line_type == 'v':
        if c < cols - 1 and _count_box_sides(game_state, r, c) == 2:
            count += 1
        if c > 0 and _count_box_sides(game_state, r, c - 1) == 2:
            count += 1
    return count

# --- Heuristic Evaluation Function ---

def evaluate_board_heuristic(game_state, player_perspective):
    """
    Evaluates the board state from the perspective of `player_perspective`.
    Higher scores are better for `player_perspective`.

    Args:
        game_state (dict): The current game state.
        player_perspective (int): The player (1 or 2) for whom we evaluate.

    Returns:
        float: The estimated heuristic value of the board state.
    """
    if game_logic.is_game_over(game_state):
        winner = game_logic.get_winner(game_state)
        if winner == player_perspective:
            return math.inf # Win is best
        elif winner == 0:
            return 0 # Tie is neutral
        else:
            return -math.inf # Loss is worst

    my_score = game_state['scores'][player_perspective]
    opponent_player = 3 - player_perspective
    opponent_score = game_state['scores'][opponent_player]

    score_difference = my_score - opponent_score

    # Count boxes with 2 sides (potential setups for the opponent)
    two_sided_boxes = 0
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    for r in range(rows - 1):
        for c in range(cols - 1):
            if _count_box_sides(game_state, r, c) == 2:
                two_sided_boxes += 1

    # Heuristic: Score difference is primary, penalize leaving 2-sided boxes.
    # Weights can be tuned. Higher score_weight means score is more important.
    # Negative two_sided_weight means we want fewer 2-sided boxes.
    score_weight = 100.0
    two_sided_weight = -2.0 # Penalize leaving setups

    heuristic_value = (score_weight * score_difference) + (two_sided_weight * two_sided_boxes)

    return heuristic_value


# --- Minimax Implementation ---

def minimax_eval(eval_state, depth, is_maximizing_player, player_perspective):
    """Recursive helper for Minimax."""
    current_player_in_state = eval_state['current_player']

    if depth == 0 or game_logic.is_game_over(eval_state):
        # Evaluate from the perspective of the player who started the search
        return evaluate_board_heuristic(eval_state, player_perspective)

    valid_moves = _get_all_valid_moves(eval_state)
    if not valid_moves: # Should only happen if game is over, caught above, but safety check
         return evaluate_board_heuristic(eval_state, player_perspective)


    if is_maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            # Simulate the move on a deep copy
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2]) # Modifies state_copy

            if boxes_completed > 0:
                # Same player moves again, same perspective, same depth
                eval_score = minimax_eval(state_copy, depth, True, player_perspective)
            else:
                # Player switches, perspective flips, depth decreases
                game_logic.switch_player(state_copy) # Switch player in the copy
                eval_score = minimax_eval(state_copy, depth - 1, False, player_perspective)

            max_eval = max(max_eval, eval_score)
        return max_eval
    else: # Minimizing player
        min_eval = math.inf
        for move in valid_moves:
            # Simulate the move on a deep copy
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

            if boxes_completed > 0:
                # Same player moves again, same perspective, same depth
                eval_score = minimax_eval(state_copy, depth, False, player_perspective)
            else:
                # Player switches, perspective flips, depth decreases
                game_logic.switch_player(state_copy)
                eval_score = minimax_eval(state_copy, depth - 1, True, player_perspective)

            min_eval = min(min_eval, eval_score)
        return min_eval

def get_minimax_move(game_state):
    """Policy 6: Uses Minimax search to find the best move."""
    ai_player_num = game_state['current_player']
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    best_score = -math.inf
    best_move = None

    for move in valid_moves:
        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            # AI gets another turn immediately in the simulation
            move_score = minimax_eval(state_copy, DEFAULT_SEARCH_DEPTH, True, ai_player_num)
        else:
            # Opponent's turn next in the simulation
            game_logic.switch_player(state_copy)
            move_score = minimax_eval(state_copy, DEFAULT_SEARCH_DEPTH - 1, False, ai_player_num)

        if move_score > best_score:
            best_score = move_score
            best_move = move
        # Optional: Add randomness for equally good moves
        elif move_score == best_score and random.choice([True, False]):
             best_move = move


    # If no move improves score (e.g., all lead to loss), pick one randomly
    if best_move is None:
        best_move = random.choice(valid_moves)

    return best_move


# --- Alpha-Beta Pruning Implementation ---

def alphabeta_eval(eval_state, depth, alpha, beta, is_maximizing_player, player_perspective):
    """Recursive helper for Alpha-Beta."""
    current_player_in_state = eval_state['current_player']

    if depth == 0 or game_logic.is_game_over(eval_state):
        return evaluate_board_heuristic(eval_state, player_perspective)

    valid_moves = _get_all_valid_moves(eval_state)
    if not valid_moves:
         return evaluate_board_heuristic(eval_state, player_perspective)

    # --- Move Ordering (Optional but Recommended for Alpha-Beta Performance) ---
    # Simple heuristic: prioritize moves that complete boxes, then safe moves.
    ordered_moves = sorted(valid_moves, key=lambda m: (
        _completes_box(eval_state, m[0], m[1], m[2]), # Completing moves first (True > False)
        not _adds_third_line(eval_state, m[0], m[1], m[2]) # Safe moves next (True > False)
    ), reverse=True) # reverse=True to put True (completing/safe) first

    if is_maximizing_player:
        max_eval = -math.inf
        for move in ordered_moves: # Use ordered moves
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

            if boxes_completed > 0:
                eval_score = alphabeta_eval(state_copy, depth, alpha, beta, True, player_perspective)
            else:
                game_logic.switch_player(state_copy)
                eval_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, False, player_perspective)

            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval) # Update alpha
            if beta <= alpha:
                break # Prune
        return max_eval
    else: # Minimizing player
        min_eval = math.inf
        for move in ordered_moves: # Use ordered moves
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

            if boxes_completed > 0:
                eval_score = alphabeta_eval(state_copy, depth, alpha, beta, False, player_perspective)
            else:
                game_logic.switch_player(state_copy)
                eval_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, True, player_perspective)

            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval) # Update beta
            if beta <= alpha:
                break # Prune
        return min_eval


def get_alphabeta_move(game_state):
    """Policy 7: Uses Minimax with Alpha-Beta Pruning."""
    ai_player_num = game_state['current_player']
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    best_score = -math.inf
    best_move = None
    alpha = -math.inf
    beta = math.inf

    # Move ordering at the root as well
    ordered_moves = sorted(valid_moves, key=lambda m: (
        _completes_box(game_state, m[0], m[1], m[2]),
        not _adds_third_line(game_state, m[0], m[1], m[2])
    ), reverse=True)

    for move in ordered_moves:
        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            # AI gets another turn, start recursive call as maximizing
            move_score = alphabeta_eval(state_copy, DEFAULT_SEARCH_DEPTH, alpha, beta, True, ai_player_num)
        else:
            # Opponent's turn next, start recursive call as minimizing
            game_logic.switch_player(state_copy)
            move_score = alphabeta_eval(state_copy, DEFAULT_SEARCH_DEPTH - 1, alpha, beta, False, ai_player_num)

        # print(f"Move {move}: Score {move_score}") # Debugging

        if move_score > best_score:
            best_score = move_score
            best_move = move

        # Update alpha at the root for the maximizing player (the AI)
        alpha = max(alpha, best_score)

        # Note: We don't prune at the root itself, pruning happens in recursive calls.

    # Fallback if no move seems good
    if best_move is None:
         best_move = random.choice(valid_moves) # Or ordered_moves[0]

    return best_move


# --- Policy Implementations ---

def get_random_move(game_state):
    """Policy 1: Plays any valid move randomly."""
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves:
        print("Warning: No valid moves found for Random Mover!")
        return None
    return random.choice(valid_moves)

def get_greedy_box_taker_move(game_state):
    """Policy 2: Takes any box if possible, otherwise plays randomly."""
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    completing_moves = []
    non_completing_moves = []
    for move in valid_moves:
        # Need to simulate move completion to check accurately
        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
        if boxes_completed > 0:
            completing_moves.append(move)
        else:
            non_completing_moves.append(move)

    if completing_moves:
        return random.choice(completing_moves) # Take one of the available boxes
    elif non_completing_moves:
        return random.choice(non_completing_moves) # Fallback to random non-completing move
    else: # Should only happen if game over
        return None


def get_cautious_move(game_state):
    """Policy 3: Avoids adding the 3rd line to a box if possible, otherwise plays randomly."""
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    safe_moves = []
    unsafe_moves = []
    completing_moves = [] # Also track completing moves separately

    for move in valid_moves:
        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
             completing_moves.append(move) # Even if completing, check if safe
             # A move completing a box *might* not add a 3rd line to *another* box
             if not _adds_third_line(game_state, move[0], move[1], move[2]):
                  # This check is slightly ambiguous. A move completing a box *by definition*
                  # adds the 4th line. Let's focus on not creating *new* 3-sided boxes.
                  # Re-evaluate: safe means doesn't create a 3-sided box *for the opponent*.
                  # If a move completes a box, the player moves again, so it's "safe" in that sense.
                  pass # Completing moves are handled differently by cautious logic

        elif not _adds_third_line(game_state, move[0], move[1], move[2]):
             safe_moves.append(move)
        else:
             unsafe_moves.append(move)


    # Cautious prioritizes *not giving away* boxes. Completing is secondary/ignored.
    if safe_moves:
        return random.choice(safe_moves)
    elif completing_moves:
        # If only completing moves or unsafe moves left, a purely cautious bot might
        # prefer an unsafe move over completing? This seems wrong.
        # Let's refine: Prefer safe non-completing, then completing, then unsafe.
         return random.choice(completing_moves) # Refined: Take box if only option besides unsafe
    elif unsafe_moves:
        return random.choice(unsafe_moves) # Forced unsafe move
    else:
         print("Warning: Cautious Mover found no moves!")
         return None


def get_greedy_cautious_move(game_state):
    """Policy 4: Combines Greedy and Cautious.
    1. Take a box if possible.
    2. If not, play a 'safe' move (doesn't add 3rd line).
    3. If not, play randomly among the 'unsafe' moves.
    """
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    completing_moves = []
    safe_non_completing_moves = []
    unsafe_non_completing_moves = []

    for move in valid_moves:
        # Simulate to check completion accurately
        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            completing_moves.append(move)
        elif not _adds_third_line(game_state, move[0], move[1], move[2]):
            safe_non_completing_moves.append(move)
        else:
            unsafe_non_completing_moves.append(move)

    if completing_moves:
        return random.choice(completing_moves)          # Priority 1: Take box
    elif safe_non_completing_moves:
        return random.choice(safe_non_completing_moves) # Priority 2: Play safe non-completing
    elif unsafe_non_completing_moves:
        return random.choice(unsafe_non_completing_moves) # Priority 3: Forced unsafe move
    else:
         print("Warning: GreedyCautious Mover found no moves!")
         return None

def get_minimal_sacrifice_move(game_state):
    """Policy 5: Like Greedy+Cautious, but when forced to make an unsafe move,
    chooses the one that adds the third line to the fewest potential boxes (usually 1 vs 2).
    """
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    completing_moves = []
    safe_non_completing_moves = []
    unsafe_moves_data = [] # Store as (move, sacrifice_count)

    for move in valid_moves:
        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            completing_moves.append(move)
        elif not _adds_third_line(game_state, move[0], move[1], move[2]):
            safe_non_completing_moves.append(move)
        else:
            # This move is unsafe (adds a 3rd line), calculate sacrifice count
            sacrifice_count = _third_line_sacrifice_count(game_state, move[0], move[1], move[2])
            unsafe_moves_data.append({'move': move, 'sacrifice': sacrifice_count})

    if completing_moves:
        return random.choice(completing_moves)              # Priority 1: Take box
    elif safe_non_completing_moves:
        return random.choice(safe_non_completing_moves)     # Priority 2: Play safe non-completing
    elif unsafe_moves_data:
        # Priority 3: Forced unsafe move - choose the minimal sacrifice
        min_sacrifice = min(item['sacrifice'] for item in unsafe_moves_data)
        best_unsafe_moves = [item['move'] for item in unsafe_moves_data if item['sacrifice'] == min_sacrifice]
        return random.choice(best_unsafe_moves) # Pick randomly among the best sacrifices
    else:
         print("Warning: MinimalSacrifice Mover found no moves!")
         return None


POLICY_MAP = {
    "Random": get_random_move,
    "Greedy": get_greedy_box_taker_move,
    "Cautious": get_cautious_move,
    "Greedy+Cautious": get_greedy_cautious_move,
    "Minimal Sacrifice": get_minimal_sacrifice_move,
    "Minimax": get_minimax_move,
    "AlphaBeta": get_alphabeta_move,
    # Add Heuristic Search policy here when implemented
}

POLICY_NAMES = list(POLICY_MAP.keys())