# ai_player.py

import random
import game_logic
import copy
import math
import time

# ... (Keep constants, helpers, heuristic, recursive eval functions as before) ...
DEFAULT_SEARCH_DEPTH = 4
DEFAULT_TIME_LIMIT = 1

# --- Helper Functions ---
# ... (unchanged) ...
def _get_all_valid_moves(game_state):
    valid_moves = []
    rows = game_state['board_rows']; cols = game_state['board_cols']
    for r in range(rows):
        for c in range(cols - 1):
            if game_logic.is_valid_line(game_state, 'h', r, c): valid_moves.append(('h', r, c))
    for r in range(rows - 1):
        for c in range(cols):
            if game_logic.is_valid_line(game_state, 'v', r, c): valid_moves.append(('v', r, c))
    return valid_moves

def _count_box_sides(game_state, box_r, box_c):
    rows = game_state['board_rows']; cols = game_state['board_cols']
    if not (0 <= box_r < rows - 1 and 0 <= box_c < cols - 1): return 0
    count = 0; h_lines = game_state['horizontal_lines']; v_lines = game_state['vertical_lines']
    if (box_r, box_c) in h_lines: count += 1
    if (box_r + 1, box_c) in h_lines: count += 1
    if (box_r, box_c) in v_lines: count += 1
    if (box_r, box_c + 1) in v_lines: count += 1
    return count

def _completes_box(game_state, line_type, r, c):
    rows = game_state['board_rows']; cols = game_state['board_cols']
    temp_h = game_state['horizontal_lines'].copy(); temp_v = game_state['vertical_lines'].copy()
    if line_type == 'h': temp_h.add((r, c))
    else: temp_v.add((r, c))
    temp_state = {'horizontal_lines': temp_h, 'vertical_lines': temp_v, 'board_rows': rows, 'board_cols': cols}
    boxes_completed = 0
    if line_type == 'h':
        if r < rows - 1 and _count_box_sides(temp_state, r, c) == 4: boxes_completed += 1
        if r > 0 and _count_box_sides(temp_state, r - 1, c) == 4: boxes_completed += 1
    elif line_type == 'v':
        if c < cols - 1 and _count_box_sides(temp_state, r, c) == 4: boxes_completed += 1
        if c > 0 and _count_box_sides(temp_state, r, c - 1) == 4: boxes_completed += 1
    return boxes_completed > 0

def _adds_third_line(game_state, line_type, r, c):
    rows = game_state['board_rows']; cols = game_state['board_cols']
    if line_type == 'h':
        if r < rows - 1 and _count_box_sides(game_state, r, c) == 2: return True
        if r > 0 and _count_box_sides(game_state, r - 1, c) == 2: return True
    elif line_type == 'v':
        if c < cols - 1 and _count_box_sides(game_state, r, c) == 2: return True
        if c > 0 and _count_box_sides(game_state, r, c - 1) == 2: return True
    return False

def _third_line_sacrifice_count(game_state, line_type, r, c):
    count = 0; rows = game_state['board_rows']; cols = game_state['board_cols']
    if line_type == 'h':
        if r < rows - 1 and _count_box_sides(game_state, r, c) == 2: count += 1
        if r > 0 and _count_box_sides(game_state, r - 1, c) == 2: count += 1
    elif line_type == 'v':
        if c < cols - 1 and _count_box_sides(game_state, r, c) == 2: count += 1
        if c > 0 and _count_box_sides(game_state, r, c - 1) == 2: count += 1
    return count

# --- Heuristic ---
def evaluate_board_heuristic(game_state, player_perspective):
    # ... (unchanged) ...
    if game_logic.is_game_over(game_state):
        winner = game_logic.get_winner(game_state)
        if winner == player_perspective: return math.inf
        elif winner == 0: return 0
        else: return -math.inf
    my_score = game_state['scores'][player_perspective]
    opponent_player = 3 - player_perspective
    opponent_score = game_state['scores'][opponent_player]
    score_diff = my_score - opponent_score
    two_sided = 0; rows = game_state['board_rows']; cols = game_state['board_cols']
    for r in range(rows - 1):
        for c in range(cols - 1):
            if _count_box_sides(game_state, r, c) == 2: two_sided += 1
    score_weight = 100.0; two_sided_weight = -2.0
    return (score_weight * score_diff) + (two_sided_weight * two_sided)


# --- Minimax Eval ---
def minimax_eval(eval_state, depth, is_maximizing_player, player_perspective, start_time, time_limit):
    # ... (unchanged - time check logic is inside) ...
    if depth == 0 or game_logic.is_game_over(eval_state):
        return evaluate_board_heuristic(eval_state, player_perspective)
    valid_moves = _get_all_valid_moves(eval_state)
    if not valid_moves: return evaluate_board_heuristic(eval_state, player_perspective)

    if is_maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0:
                eval_score = minimax_eval(state_copy, depth, True, player_perspective, start_time, time_limit)
            else:
                game_logic.switch_player(state_copy)
                eval_score = minimax_eval(state_copy, depth - 1, False, player_perspective, start_time, time_limit)
            max_eval = max(max_eval, eval_score)
        return max_eval
    else: # Minimizing
        min_eval = math.inf
        for move in valid_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0:
                eval_score = minimax_eval(state_copy, depth, False, player_perspective, start_time, time_limit)
            else:
                game_logic.switch_player(state_copy)
                eval_score = minimax_eval(state_copy, depth - 1, True, player_perspective, start_time, time_limit)
            min_eval = min(min_eval, eval_score)
        return min_eval

# --- Get Minimax Move (Revised Fallback) ---
def get_minimax_move(game_state, depth=DEFAULT_SEARCH_DEPTH, time_limit=DEFAULT_TIME_LIMIT):
    start_time = time.monotonic()
    ai_player_num = game_state['current_player']
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    best_score = -math.inf
    best_move = None # Initialize best_move to None
    moves_evaluated_count = 0 # Track if any move evaluation completed

    # Try to use ordered moves for potential minor benefit even without pruning
    ordered_moves = sorted(valid_moves, key=lambda m: (
        _completes_box(game_state, m[0], m[1], m[2]),
        not _adds_third_line(game_state, m[0], m[1], m[2])
    ), reverse=True)

    for move in ordered_moves: # Use ordered moves
        if time.monotonic() - start_time > time_limit:
            print(f" Minimax time limit reached after evaluating {moves_evaluated_count} root move(s).")
            break # Stop evaluating more root moves

        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            move_score = minimax_eval(state_copy, depth, True, ai_player_num, start_time, time_limit)
        else:
            game_logic.switch_player(state_copy)
            move_score = minimax_eval(state_copy, depth - 1, False, ai_player_num, start_time, time_limit)

        moves_evaluated_count += 1

        # --- Update best move based on score ---
        if best_move is None or move_score > best_score: # Assign the first evaluated move, or if better
            best_score = move_score
            best_move = move
        elif move_score == best_score: # Randomly pick between equally good moves
            if random.choice([True, False]):
                 best_move = move

    # --- Refined Fallback ---
    # If the loop finished or broke, but best_move is *still* None, it means
    # the time limit was hit *before* the first move's evaluation could even return.
    if best_move is None:
        print(" Minimax fallback: No move evaluation completed within time limit. Choosing first valid move.")
        # Fallback to the first move in the ordered list (or just valid_moves[0])
        best_move = ordered_moves[0] if ordered_moves else None # Ensure list isn't empty

    # elapsed_time = time.monotonic() - start_time
    # print(f" Minimax Search Time: {elapsed_time:.4f}s")
    return best_move


# --- AlphaBeta Eval ---
def alphabeta_eval(eval_state, depth, alpha, beta, is_maximizing_player, player_perspective, start_time, time_limit):
    # ... (unchanged - time check logic is inside) ...
    if depth == 0 or game_logic.is_game_over(eval_state):
        return evaluate_board_heuristic(eval_state, player_perspective)
    valid_moves = _get_all_valid_moves(eval_state)
    if not valid_moves: return evaluate_board_heuristic(eval_state, player_perspective)
    ordered_moves = sorted(valid_moves, key=lambda m: (_completes_box(eval_state, m[0], m[1], m[2]), not _adds_third_line(eval_state, m[0], m[1], m[2])), reverse=True)

    if is_maximizing_player:
        max_eval = -math.inf
        for move in ordered_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0:
                eval_score = alphabeta_eval(state_copy, depth, alpha, beta, True, player_perspective, start_time, time_limit)
            else:
                game_logic.switch_player(state_copy)
                eval_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, False, player_perspective, start_time, time_limit)
            max_eval = max(max_eval, eval_score); alpha = max(alpha, max_eval)
            if beta <= alpha: break # Prune
        return max_eval
    else: # Minimizing
        min_eval = math.inf
        for move in ordered_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0:
                eval_score = alphabeta_eval(state_copy, depth, alpha, beta, False, player_perspective, start_time, time_limit)
            else:
                game_logic.switch_player(state_copy)
                eval_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, True, player_perspective, start_time, time_limit)
            min_eval = min(min_eval, eval_score); beta = min(beta, min_eval)
            if beta <= alpha: break # Prune
        return min_eval


# --- Get AlphaBeta Move (Revised Fallback) ---
def get_alphabeta_move(game_state, depth=DEFAULT_SEARCH_DEPTH, time_limit=DEFAULT_TIME_LIMIT):
    start_time = time.monotonic()
    ai_player_num = game_state['current_player']
    valid_moves = _get_all_valid_moves(game_state)
    if not valid_moves: return None

    best_score = -math.inf
    best_move = None # Initialize best_move to None
    alpha = -math.inf
    beta = math.inf
    moves_evaluated_count = 0 # Track if any move evaluation completed

    ordered_moves = sorted(valid_moves, key=lambda m: (
        _completes_box(game_state, m[0], m[1], m[2]),
        not _adds_third_line(game_state, m[0], m[1], m[2])
    ), reverse=True)

    for move in ordered_moves:
        if time.monotonic() - start_time > time_limit:
            print(f" AB time limit reached after evaluating {moves_evaluated_count} root move(s).")
            break # Stop evaluating more root moves

        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        # Determine perspective for the recursive call
        if boxes_completed > 0:
            move_score = alphabeta_eval(state_copy, depth, alpha, beta, True, ai_player_num, start_time, time_limit)
        else:
            game_logic.switch_player(state_copy)
            move_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, False, ai_player_num, start_time, time_limit)

        moves_evaluated_count += 1

        # --- Update best move based on score ---
        # Crucially, update if it's the first move evaluated OR if the score is better
        if best_move is None or move_score > best_score:
            best_score = move_score
            best_move = move
            # Update alpha only when best_score improves for the maximizer (root)
            alpha = max(alpha, best_score)
        elif move_score == best_score: # Randomly pick between equally good moves
            if random.choice([True, False]):
                 best_move = move
            # Alpha doesn't change if score isn't strictly better

    # --- Refined Fallback ---
    # If the loop finished or broke, but best_move is *still* None, it means
    # the time limit was hit *before* the first move's evaluation could even return.
    if best_move is None:
        print(" AB fallback: No move evaluation completed within time limit. Choosing first valid move.")
        # Fallback to the first move in the ordered list
        best_move = ordered_moves[0] if ordered_moves else None

    # elapsed_time = time.monotonic() - start_time
    # print(f" AlphaBeta Search Time: {elapsed_time:.4f}s")
    return best_move


# --- Simple Policies (unchanged) ---
def get_random_move(game_state):
    valid_moves = _get_all_valid_moves(game_state); return random.choice(valid_moves) if valid_moves else None
def get_greedy_box_taker_move(game_state):
    valid_moves = _get_all_valid_moves(game_state); comp = []; non_comp = []
    if not valid_moves: return None
    for m in valid_moves:
        sc = copy.deepcopy(game_state); boxes = game_logic.make_move(sc, m[0], m[1], m[2])
        if boxes > 0: comp.append(m)
        else: non_comp.append(m)
    if comp: return random.choice(comp)
    elif non_comp: return random.choice(non_comp)
    else: return None
def get_cautious_move(game_state):
    valid_moves = _get_all_valid_moves(game_state); safe, unsafe, comp = [], [], []
    if not valid_moves: return None
    for m in valid_moves:
        sc = copy.deepcopy(game_state); boxes = game_logic.make_move(sc, m[0], m[1], m[2])
        if boxes > 0: comp.append(m)
        elif not _adds_third_line(game_state, m[0], m[1], m[2]): safe.append(m)
        else: unsafe.append(m)
    if safe: return random.choice(safe)
    elif comp: return random.choice(comp)
    elif unsafe: return random.choice(unsafe)
    else: return None
def get_greedy_cautious_move(game_state):
    valid_moves = _get_all_valid_moves(game_state); comp, safe, unsafe = [], [], []
    if not valid_moves: return None
    for m in valid_moves:
        sc = copy.deepcopy(game_state); boxes = game_logic.make_move(sc, m[0], m[1], m[2])
        if boxes > 0: comp.append(m)
        elif not _adds_third_line(game_state, m[0], m[1], m[2]): safe.append(m)
        else: unsafe.append(m)
    if comp: return random.choice(comp)
    elif safe: return random.choice(safe)
    elif unsafe: return random.choice(unsafe)
    else: return None
def get_minimal_sacrifice_move(game_state):
    valid_moves = _get_all_valid_moves(game_state); comp, safe, unsafe_data = [], [], []
    if not valid_moves: return None
    for m in valid_moves:
        sc = copy.deepcopy(game_state); boxes = game_logic.make_move(sc, m[0], m[1], m[2])
        if boxes > 0: comp.append(m)
        elif not _adds_third_line(game_state, m[0], m[1], m[2]): safe.append(m)
        else: unsafe_data.append({'move': m, 'sacrifice': _third_line_sacrifice_count(game_state, m[0], m[1], m[2])})
    if comp: return random.choice(comp)
    elif safe: return random.choice(safe)
    elif unsafe_data:
        min_sac = min(item['sacrifice'] for item in unsafe_data)
        best_unsafe = [item['move'] for item in unsafe_data if item['sacrifice'] == min_sac]
        return random.choice(best_unsafe)
    else: return None

# --- Policy Map ---
POLICY_MAP = {
    "Random": get_random_move,
    "Greedy": get_greedy_box_taker_move,
    "Cautious": get_cautious_move,
    "Greedy+Cautious": get_greedy_cautious_move,
    "Minimal Sacrifice": get_minimal_sacrifice_move,
    "Minimax": lambda gs: get_minimax_move(gs, DEFAULT_SEARCH_DEPTH, DEFAULT_TIME_LIMIT),
    "AlphaBeta": lambda gs: get_alphabeta_move(gs, DEFAULT_SEARCH_DEPTH, DEFAULT_TIME_LIMIT),
}
POLICY_NAMES = list(POLICY_MAP.keys())