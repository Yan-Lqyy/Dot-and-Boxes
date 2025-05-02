# ai_minimax_ab.py
"""
Implementations of Minimax and AlphaBeta search policies.
Includes the heuristic evaluation function.
"""
import copy
import math
import time
import random
import game_logic

# Import necessary helpers
from ai_helpers import get_all_valid_moves, count_box_sides, completes_box, adds_third_line

# --- Constants specific to these algorithms ---
DEFAULT_SEARCH_DEPTH = 4 # Default depth if not specified otherwise

# --- Heuristic Evaluation Function ---
def evaluate_board_heuristic(game_state, player_perspective):
    """Evaluates the board state from the perspective of `player_perspective`."""
    if game_logic.is_game_over(game_state):
        winner = game_logic.get_winner(game_state)
        if winner == player_perspective: return math.inf
        elif winner == 0: return 0
        else: return -math.inf

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
            # Check box validity before counting sides
            if count_box_sides(game_state, r, c) == 2:
                two_sided_boxes += 1

    # Heuristic weights (can be tuned)
    score_weight = 100.0
    two_sided_weight = -2.0 # Penalize leaving setups

    heuristic_value = (score_weight * score_difference) + (two_sided_weight * two_sided_boxes)
    return heuristic_value


# --- Minimax Implementation with Time Limit ---
def minimax_eval(eval_state, depth, is_maximizing_player, player_perspective, start_time, time_limit):
    """Recursive helper for Minimax with time limit."""
    if depth == 0 or game_logic.is_game_over(eval_state):
        return evaluate_board_heuristic(eval_state, player_perspective)

    # Check time *before* getting moves and recursing further
    if time.monotonic() - start_time > time_limit:
         # print(f" Minimax Time limit reached at depth {depth} (eval)")
         return evaluate_board_heuristic(eval_state, player_perspective) # Return heuristic of current state

    valid_moves = get_all_valid_moves(eval_state)
    if not valid_moves:
        return evaluate_board_heuristic(eval_state, player_perspective)

    if is_maximizing_player:
        max_eval = -math.inf
        for move in valid_moves:
            # Check time again before deep copy and recursion for *this* move
            if time.monotonic() - start_time > time_limit: break

            state_copy = copy.deepcopy(eval_state)
            boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

            if boxes_completed > 0:
                eval_score = minimax_eval(state_copy, depth, True, player_perspective, start_time, time_limit)
            else:
                game_logic.switch_player(state_copy)
                eval_score = minimax_eval(state_copy, depth - 1, False, player_perspective, start_time, time_limit)
            max_eval = max(max_eval, eval_score)
        return max_eval # Return best score found *within time limit* for this node
    else: # Minimizing player
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
        return min_eval # Return best score found *within time limit* for this node

def get_minimax_move(game_state, depth=DEFAULT_SEARCH_DEPTH, time_limit=None):
    """Policy entry point: Uses Minimax search."""
    start_time = time.monotonic()
    ai_player_num = game_state['current_player']
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return None

    best_score = -math.inf
    best_move = None
    moves_evaluated_count = 0

    ordered_moves = sorted(valid_moves, key=lambda m: (
        completes_box(game_state, m[0], m[1], m[2]),
        not adds_third_line(game_state, m[0], m[1], m[2])
    ), reverse=True)

    for move in ordered_moves:
        if time_limit is not None and time.monotonic() - start_time > time_limit:
            # print(f" Minimax time limit reached after evaluating {moves_evaluated_count} root move(s).")
            break

        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            move_score = minimax_eval(state_copy, depth, True, ai_player_num, start_time, time_limit if time_limit is not None else float('inf'))
        else:
            game_logic.switch_player(state_copy)
            move_score = minimax_eval(state_copy, depth - 1, False, ai_player_num, start_time, time_limit if time_limit is not None else float('inf'))

        moves_evaluated_count += 1
        if best_move is None or move_score > best_score:
            best_score = move_score
            best_move = move
        elif move_score == best_score and random.choice([True, False]):
             best_move = move

    if best_move is None:
        # print(" Minimax fallback: No evaluation completed or all moves bad. Choosing first valid move.")
        best_move = ordered_moves[0] if ordered_moves else None

    return best_move


# --- Alpha-Beta Pruning Implementation with Time Limit ---
def alphabeta_eval(eval_state, depth, alpha, beta, is_maximizing_player, player_perspective, start_time, time_limit):
    """Recursive helper for Alpha-Beta with time limit."""
    if depth == 0 or game_logic.is_game_over(eval_state):
        return evaluate_board_heuristic(eval_state, player_perspective)

    # Check time *before* getting moves and recursing further
    if time.monotonic() - start_time > time_limit:
         # print(f" AB Time limit reached at depth {depth} (eval)")
         return evaluate_board_heuristic(eval_state, player_perspective) # Return heuristic

    valid_moves = get_all_valid_moves(eval_state)
    if not valid_moves:
         return evaluate_board_heuristic(eval_state, player_perspective)

    ordered_moves = sorted(valid_moves, key=lambda m: (
        completes_box(eval_state, m[0], m[1], m[2]),
        not adds_third_line(eval_state, m[0], m[1], m[2])
    ), reverse=True)

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

            max_eval = max(max_eval, eval_score)
            alpha = max(alpha, max_eval)
            if beta <= alpha:
                break # Prune
        return max_eval # Return best score found *within time limit* for this node
    else: # Minimizing player
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

            min_eval = min(min_eval, eval_score)
            beta = min(beta, min_eval)
            if beta <= alpha:
                break # Prune
        return min_eval # Return best score found *within time limit* for this node

def get_alphabeta_move(game_state, depth=DEFAULT_SEARCH_DEPTH, time_limit=None):
    """Policy entry point: Uses Minimax with Alpha-Beta Pruning."""
    start_time = time.monotonic()
    ai_player_num = game_state['current_player']
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return None

    best_score = -math.inf
    best_move = None
    alpha = -math.inf
    beta = math.inf
    moves_evaluated_count = 0

    ordered_moves = sorted(valid_moves, key=lambda m: (
        completes_box(game_state, m[0], m[1], m[2]),
        not adds_third_line(game_state, m[0], m[1], m[2])
    ), reverse=True)

    for move in ordered_moves:
        if time_limit is not None and time.monotonic() - start_time > time_limit:
            # print(f" AB time limit reached after evaluating {moves_evaluated_count} root move(s).")
            break

        state_copy = copy.deepcopy(game_state)
        boxes_completed = game_logic.make_move(state_copy, move[0], move[1], move[2])

        if boxes_completed > 0:
            move_score = alphabeta_eval(state_copy, depth, alpha, beta, True, ai_player_num, start_time, time_limit if time_limit is not None else float('inf'))
        else:
            game_logic.switch_player(state_copy)
            move_score = alphabeta_eval(state_copy, depth - 1, alpha, beta, False, ai_player_num, start_time, time_limit if time_limit is not None else float('inf'))

        moves_evaluated_count += 1
        if best_move is None or move_score > best_score:
            best_score = move_score
            best_move = move
            alpha = max(alpha, best_score) # Update alpha at the root
        elif move_score == best_score and random.choice([True, False]):
             best_move = move

    if best_move is None:
        # print(" AB fallback: No evaluation completed or all moves bad. Choosing first valid move.")
        best_move = ordered_moves[0] if ordered_moves else None

    return best_move