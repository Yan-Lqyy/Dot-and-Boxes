# ai_minimax_ab.py
"""Implementations of Minimax and AlphaBeta search policies."""
import copy
import math
import time
import random
import game_logic
from ai_helpers import get_all_valid_moves, count_box_sides, completes_box, adds_third_line

DEFAULT_SEARCH_DEPTH = 4

# --- Heuristic (Unchanged) ---
def evaluate_board_heuristic(game_state, player_perspective):
    # ... (implementation as before) ...
    if game_logic.is_game_over(game_state):
        winner = game_logic.get_winner(game_state)
        if winner == player_perspective: return math.inf
        elif winner == 0: return 0
        else: return -math.inf
    my_score = game_state['scores'][player_perspective]; opp_score = game_state['scores'][3 - player_perspective]
    score_diff = my_score - opp_score
    two_sided = 0; rows = game_state['board_rows']; cols = game_state['board_cols']
    for r in range(rows - 1):
        for c in range(cols - 1):
            if count_box_sides(game_state, r, c) == 2: two_sided += 1
    return (100.0 * score_diff) + (-2.0 * two_sided)

# --- Minimax Eval (Unchanged internal logic, just returns score) ---
def minimax_eval(eval_state, depth, is_maximizing_player, player_perspective, start_time, time_limit):
    # ... (implementation as before, including internal time checks returning heuristic value on timeout) ...
    if depth == 0 or game_logic.is_game_over(eval_state): return evaluate_board_heuristic(eval_state, player_perspective)
    if time.monotonic() - start_time > time_limit: return evaluate_board_heuristic(eval_state, player_perspective)
    valid_moves = get_all_valid_moves(eval_state)
    if not valid_moves: return evaluate_board_heuristic(eval_state, player_perspective)
    if is_maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state); boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0: eval_score = minimax_eval(state_copy, depth, True, player_perspective, start_time, time_limit)
            else: game_logic.switch_player(state_copy); eval_score = minimax_eval(state_copy, depth - 1, False, player_perspective, start_time, time_limit)
            max_eval = max(max_eval, eval_score)
        return max_eval
    else: # Minimizing
        min_eval = math.inf
        for move in valid_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state); boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0: eval_score = minimax_eval(state_copy, depth, False, player_perspective, start_time, time_limit)
            else: game_logic.switch_player(state_copy); eval_score = minimax_eval(state_copy, depth - 1, True, player_perspective, start_time, time_limit)
            min_eval = min(min_eval, eval_score)
        return min_eval

# --- Get Minimax Move (Track stop reason) ---
def get_minimax_move(game_state, depth=DEFAULT_SEARCH_DEPTH, time_limit=None):
    """Policy entry point: Uses Minimax search."""
    start_time = time.monotonic()
    ai_player_num = game_state['current_player']
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return {'move': None, 'stop_reason': 'No Valid Moves'}

    best_score = -math.inf
    best_move = None
    moves_evaluated_count = 0
    time_limit_hit = False
    actual_time_limit = time_limit if time_limit is not None else float('inf')

    ordered_moves = sorted(valid_moves, key=lambda m: (completes_box(game_state, m[0], m[1], m[2]), not adds_third_line(game_state, m[0], m[1], m[2])), reverse=True)

    for move in ordered_moves:
        if time.monotonic() - start_time > actual_time_limit:
            time_limit_hit = True
            # print(f" Minimax time limit hit before evaluating move {move}.")
            break

        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        # Pass actual_time_limit to recursive call
        if boxes_completed > 0:
            move_score = minimax_eval(state_copy, depth, True, ai_player_num, start_time, actual_time_limit)
        else:
            game_logic.switch_player(state_copy)
            move_score = minimax_eval(state_copy, depth - 1, False, ai_player_num, start_time, actual_time_limit)

        moves_evaluated_count += 1
        if best_move is None or move_score > best_score:
            best_score = move_score
            best_move = move
        elif move_score == best_score and random.choice([True, False]):
             best_move = move

    # Determine stop reason
    stop_reason = "Unknown"
    if best_move is None: # Fallback triggered
        stop_reason = "Fallback (No Eval Completed)"
        best_move = ordered_moves[0] if ordered_moves else None # Ensure a move is selected if possible
        if best_move is None: # Truly no moves
            stop_reason = 'No Valid Moves'
    elif time_limit_hit:
        stop_reason = f"Time Limit Reached ({moves_evaluated_count}/{len(ordered_moves)} root moves)"
    else:
        stop_reason = f"Depth Limit Reached (Depth {depth})" # Completed search to depth limit

    return {'move': best_move, 'stop_reason': stop_reason}


# --- AlphaBeta Eval (Unchanged internal logic) ---
def alphabeta_eval(eval_state, depth, alpha, beta, is_maximizing_player, player_perspective, start_time, time_limit):
    # ... (implementation as before, including internal time checks returning heuristic value on timeout) ...
    if depth == 0 or game_logic.is_game_over(eval_state): return evaluate_board_heuristic(eval_state, player_perspective)
    if time.monotonic() - start_time > time_limit: return evaluate_board_heuristic(eval_state, player_perspective) # Return heuristic on timeout
    valid_moves = get_all_valid_moves(eval_state)
    if not valid_moves: return evaluate_board_heuristic(eval_state, player_perspective)
    ordered_moves = sorted(valid_moves, key=lambda m: (completes_box(eval_state, m[0], m[1], m[2]), not adds_third_line(eval_state, m[0], m[1], m[2])), reverse=True)
    if is_maximizing_player:
        max_eval = -math.inf
        for move in ordered_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state); boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0: eval_score = alphabeta_eval(state_copy, depth, alpha, beta, True, player_perspective, start_time, time_limit)
            else: game_logic.switch_player(state_copy); eval_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, False, player_perspective, start_time, time_limit)
            max_eval = max(max_eval, eval_score); alpha = max(alpha, max_eval)
            if beta <= alpha: break
        return max_eval
    else: # Minimizing
        min_eval = math.inf
        for move in ordered_moves:
            if time.monotonic() - start_time > time_limit: break
            state_copy = copy.deepcopy(eval_state); boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])
            if boxes_completed > 0: eval_score = alphabeta_eval(state_copy, depth, alpha, beta, False, player_perspective, start_time, time_limit)
            else: game_logic.switch_player(state_copy); eval_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, True, player_perspective, start_time, time_limit)
            min_eval = min(min_eval, eval_score); beta = min(beta, min_eval)
            if beta <= alpha: break
        return min_eval

# --- Get AlphaBeta Move (Track stop reason) ---
def get_alphabeta_move(game_state, depth=DEFAULT_SEARCH_DEPTH, time_limit=None):
    """Policy entry point: Uses Minimax with Alpha-Beta Pruning."""
    start_time = time.monotonic()
    ai_player_num = game_state['current_player']
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return {'move': None, 'stop_reason': 'No Valid Moves'}

    best_score = -math.inf
    best_move = None
    alpha = -math.inf
    beta = math.inf
    moves_evaluated_count = 0
    time_limit_hit = False
    actual_time_limit = time_limit if time_limit is not None else float('inf')

    ordered_moves = sorted(valid_moves, key=lambda m: (completes_box(game_state, m[0], m[1], m[2]), not adds_third_line(game_state, m[0], m[1], m[2])), reverse=True)

    for move in ordered_moves:
        if time.monotonic() - start_time > actual_time_limit:
            time_limit_hit = True
            # print(f" AB time limit hit before evaluating move {move}.")
            break

        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        # Pass actual_time_limit to recursive call
        if boxes_completed > 0:
            move_score = alphabeta_eval(state_copy, depth, alpha, beta, True, ai_player_num, start_time, actual_time_limit)
        else:
            game_logic.switch_player(state_copy)
            move_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, False, ai_player_num, start_time, actual_time_limit)

        moves_evaluated_count += 1
        if best_move is None or move_score > best_score:
            best_score = move_score
            best_move = move
            alpha = max(alpha, best_score) # Update alpha at the root
        elif move_score == best_score and random.choice([True, False]):
             best_move = move

    # Determine stop reason
    stop_reason = "Unknown"
    if best_move is None: # Fallback triggered
        stop_reason = "Fallback (No Eval Completed)"
        best_move = ordered_moves[0] if ordered_moves else None # Ensure a move is selected if possible
        if best_move is None: # Truly no moves
             stop_reason = 'No Valid Moves'
    elif time_limit_hit:
        stop_reason = f"Time Limit Reached ({moves_evaluated_count}/{len(ordered_moves)} root moves)"
    else:
        stop_reason = f"Depth Limit Reached (Depth {depth})" # Completed search to depth limit

    return {'move': best_move, 'stop_reason': stop_reason}