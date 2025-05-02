# ai_simple_policies.py
"""Implementation of simple, reactive AI policies."""
import random
import copy
import game_logic
from ai_helpers import (get_all_valid_moves, completes_box,
                        adds_third_line, third_line_sacrifice_count)

# Consistent return format
RETURN_NA = {'move': None, 'stop_reason': 'No Valid Moves'}
STOP_REASON_SIMPLE = "N/A (Deterministic)" # Reason for simple policies

def get_random_move(game_state):
    """Policy: Plays any valid move randomly."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return RETURN_NA
    move = random.choice(valid_moves)
    return {'move': move, 'stop_reason': 'Random Choice'} # Specific reason for random

def get_greedy_box_taker_move(game_state):
    """Policy: Takes any box if possible, otherwise plays randomly."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return RETURN_NA
    completing_moves, non_completing_moves = [], []
    for m in valid_moves:
        if completes_box(game_state, m[0], m[1], m[2]): completing_moves.append(m)
        else: non_completing_moves.append(m)

    move = None
    if completing_moves: move = random.choice(completing_moves)
    elif non_completing_moves: move = random.choice(non_completing_moves)

    return {'move': move, 'stop_reason': STOP_REASON_SIMPLE} if move else RETURN_NA

def get_cautious_move(game_state):
    """Policy: Avoids adding the 3rd line if possible."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return RETURN_NA
    safe, unsafe, comp = [], [], []
    for m in valid_moves:
        if completes_box(game_state, m[0], m[1], m[2]): comp.append(m)
        elif not adds_third_line(game_state, m[0], m[1], m[2]): safe.append(m)
        else: unsafe.append(m)

    move = None
    if safe: move = random.choice(safe)
    elif comp: move = random.choice(comp)
    elif unsafe: move = random.choice(unsafe)

    return {'move': move, 'stop_reason': STOP_REASON_SIMPLE} if move else RETURN_NA

def get_greedy_cautious_move(game_state):
    """Policy: Greedy > Cautious > Unsafe."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return RETURN_NA
    comp, safe, unsafe = [], [], []
    for m in valid_moves:
        if completes_box(game_state, m[0], m[1], m[2]): comp.append(m)
        elif not adds_third_line(game_state, m[0], m[1], m[2]): safe.append(m)
        else: unsafe.append(m)

    move = None
    if comp: move = random.choice(comp)
    elif safe: move = random.choice(safe)
    elif unsafe: move = random.choice(unsafe)

    return {'move': move, 'stop_reason': STOP_REASON_SIMPLE} if move else RETURN_NA

def get_minimal_sacrifice_move(game_state):
    """Policy: Greedy > Cautious > Minimal Sacrifice Unsafe."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return RETURN_NA
    comp, safe, unsafe_data = [], [], []
    for m in valid_moves:
        if completes_box(game_state, m[0], m[1], m[2]): comp.append(m)
        elif not adds_third_line(game_state, m[0], m[1], m[2]): safe.append(m)
        else: unsafe_data.append({'move': m, 'sacrifice': third_line_sacrifice_count(game_state, m[0], m[1], m[2])})

    move = None
    if comp: move = random.choice(comp)
    elif safe: move = random.choice(safe)
    elif unsafe_data:
        min_sac = min(item['sacrifice'] for item in unsafe_data)
        best_unsafe = [item['move'] for item in unsafe_data if item['sacrifice'] == min_sac]
        move = random.choice(best_unsafe)

    return {'move': move, 'stop_reason': STOP_REASON_SIMPLE} if move else RETURN_NA