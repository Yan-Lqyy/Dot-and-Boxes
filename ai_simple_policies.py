# ai_simple_policies.py
"""
Implementation of simple, reactive AI policies.
"""
import random
import copy
import game_logic

# Import necessary helpers from the new helper file
from ai_helpers import (get_all_valid_moves, completes_box,
                        adds_third_line, third_line_sacrifice_count)


def get_random_move(game_state):
    """Policy: Plays any valid move randomly."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves:
        # print("Warning: No valid moves found for Random Mover!")
        return None
    return random.choice(valid_moves)

def get_greedy_box_taker_move(game_state):
    """Policy: Takes any box if possible, otherwise plays randomly."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return None

    completing_moves = []
    non_completing_moves = []
    for move in valid_moves:
        # Use helper to check without simulating full make_move
        if completes_box(game_state, move[0], move[1], move[2]):
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
    """Policy: Avoids adding the 3rd line if possible."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return None

    safe_moves = []
    unsafe_moves = []
    completing_moves = [] # Track separately

    for move in valid_moves:
        if completes_box(game_state, move[0], move[1], move[2]):
            completing_moves.append(move)
        elif not adds_third_line(game_state, move[0], move[1], move[2]):
            safe_moves.append(move)
        else:
            unsafe_moves.append(move)

    # Refined Cautious Logic: Prefer safe, then completing, then unsafe
    if safe_moves:
        return random.choice(safe_moves)
    elif completing_moves:
        # If only completing or unsafe left, better to complete than setup opponent
        return random.choice(completing_moves)
    elif unsafe_moves:
        return random.choice(unsafe_moves) # Forced unsafe move
    else:
        # print("Warning: Cautious Mover found no moves!")
        return None


def get_greedy_cautious_move(game_state):
    """Policy: Greedy > Cautious > Unsafe."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return None

    completing_moves = []
    safe_non_completing_moves = []
    unsafe_non_completing_moves = []

    for move in valid_moves:
        if completes_box(game_state, move[0], move[1], move[2]):
            completing_moves.append(move)
        elif not adds_third_line(game_state, move[0], move[1], move[2]):
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
        # print("Warning: GreedyCautious Mover found no moves!")
        return None

def get_minimal_sacrifice_move(game_state):
    """Policy: Greedy > Cautious > Minimal Sacrifice Unsafe."""
    valid_moves = get_all_valid_moves(game_state)
    if not valid_moves: return None

    completing_moves = []
    safe_non_completing_moves = []
    unsafe_moves_data = [] # Store as {'move': move, 'sacrifice': count}

    for move in valid_moves:
        if completes_box(game_state, move[0], move[1], move[2]):
            completing_moves.append(move)
        elif not adds_third_line(game_state, move[0], move[1], move[2]):
            safe_non_completing_moves.append(move)
        else:
            # This move is unsafe (adds a 3rd line), calculate sacrifice count
            sacrifice_count = third_line_sacrifice_count(game_state, move[0], move[1], move[2])
            unsafe_moves_data.append({'move': move, 'sacrifice': sacrifice_count})

    if completing_moves:
        return random.choice(completing_moves)              # Priority 1: Take box
    elif safe_non_completing_moves:
        return random.choice(safe_non_completing_moves)     # Priority 2: Play safe non-completing
    elif unsafe_moves_data:
        # Priority 3: Forced unsafe move - choose the minimal sacrifice
        # Handle potential edge case where list might be empty (though logic suggests it shouldn't be)
        if not unsafe_moves_data:
             # Should not be reachable if valid_moves existed and weren't completing/safe
             print("Warning: MinimalSacrifice reached unexpected empty unsafe_moves_data")
             return get_random_move(game_state) # Fallback further
        min_sacrifice = min(item['sacrifice'] for item in unsafe_moves_data)
        best_unsafe_moves = [item['move'] for item in unsafe_moves_data if item['sacrifice'] == min_sacrifice]
        return random.choice(best_unsafe_moves) # Pick randomly among the best sacrifices
    else:
        # print("Warning: MinimalSacrifice Mover found no moves!")
        return None