# game_logic.py
"""Core logic for the Dots and Boxes game."""
import copy # Keep copy for other potential uses, though not strictly needed for below

def initialize_game(side_length):
    """Initializes the game state for a square board."""
    if not (4 <= side_length <= 10):
        raise ValueError("Board side length (dots) must be between 4 and 10.")
    rows, cols = side_length, side_length
    num_boxes_r, num_boxes_c = rows - 1, cols - 1
    total_boxes = num_boxes_r * num_boxes_c

    game_state = {
        'board_rows': rows,
        'board_cols': cols,
        # *** CHANGED: Use dictionaries to store line owners ***
        'horizontal_lines': {}, # Stores {(r, c): player_num}
        'vertical_lines': {},   # Stores {(r, c): player_num}
        'box_owners': {(r, c): 0 for r in range(num_boxes_r) for c in range(num_boxes_c)},
        'scores': {1: 0, 2: 0},
        'current_player': 1,
        'total_boxes': total_boxes,
    }
    return game_state

def _get_max_indices(game_state):
    """Helper to get max row/col indices for line reference dots."""
    rows = game_state['board_rows']; cols = game_state['board_cols']
    return rows - 1, cols - 2, rows - 2, cols - 1 # max_r_h, max_c_h, max_r_v, max_c_v

def is_valid_line(game_state, line_type, r, c):
    """Checks if a line is within bounds and not already taken."""
    max_r_h, max_c_h, max_r_v, max_c_v = _get_max_indices(game_state)
    h_lines = game_state['horizontal_lines'] # Now a dict
    v_lines = game_state['vertical_lines']   # Now a dict

    if line_type == 'h':
        if not (0 <= r <= max_r_h and 0 <= c <= max_c_h): return False
        # *** CHANGED: Check if key exists in dict ***
        return (r, c) not in h_lines
    elif line_type == 'v':
        if not (0 <= r <= max_r_v and 0 <= c <= max_c_v): return False
        # *** CHANGED: Check if key exists in dict ***
        return (r, c) not in v_lines
    else:
        return False

def check_box_completion(game_state, player_who_just_moved):
    """Checks for newly completed boxes. Updates owners and returns count."""
    newly_completed_count = 0
    rows = game_state['board_rows']; cols = game_state['board_cols']
    h_lines = game_state['horizontal_lines'] # Dict
    v_lines = game_state['vertical_lines']   # Dict
    box_owners = game_state['box_owners']

    for r in range(rows - 1):
        for c in range(cols - 1):
            if box_owners.get((r, c), 0) == 0: # Check if box is unowned
                # *** CHANGED: Check for key existence in dicts ***
                has_top = (r, c) in h_lines
                has_bottom = (r + 1, c) in h_lines
                has_left = (r, c) in v_lines
                has_right = (r, c + 1) in v_lines

                if has_top and has_bottom and has_left and has_right:
                    box_owners[(r, c)] = player_who_just_moved # Assign owner
                    newly_completed_count += 1
    return newly_completed_count

def make_move(game_state, line_type, r, c):
    """Attempts to draw a line, updates state, and returns boxes completed."""
    if not is_valid_line(game_state, line_type, r, c):
        # print(f"Debug: make_move detected invalid line: {line_type}, r={r}, c={c}")
        return -1 # Invalid move

    player = game_state['current_player']

    # *** CHANGED: Add line to dict with player as value ***
    if line_type == 'h':
        game_state['horizontal_lines'][(r, c)] = player
    else: # line_type == 'v'
        game_state['vertical_lines'][(r, c)] = player

    # Check for completed boxes and update ownership/score
    boxes_completed_this_turn = check_box_completion(game_state, player)

    if boxes_completed_this_turn > 0:
         # Recalculate total score for the player based on owned boxes
         # (Safer than just adding, handles potential edge cases)
         current_player_boxes = sum(1 for owner in game_state['box_owners'].values() if owner == player)
         game_state['scores'][player] = current_player_boxes

    return boxes_completed_this_turn

def switch_player(game_state):
    """Switches the current player."""
    game_state['current_player'] = 3 - game_state['current_player']

def is_game_over(game_state):
    """Checks if all boxes have been claimed."""
    # Check if sum of scores equals total possible boxes
    return sum(game_state['scores'].values()) == game_state['total_boxes']

def get_winner(game_state):
    """Determines the winner based on scores. Returns 0 for a tie."""
    score1 = game_state['scores'][1]
    score2 = game_state['scores'][2]
    if score1 > score2: return 1
    elif score2 > score1: return 2
    else: return 0 # Tie