# ai_helpers.py
"""
Common helper functions used by various AI policies.
"""
import game_logic
import copy
import math # Keep math if needed by any helper, maybe not strictly necessary here


def get_all_valid_moves(game_state):
    """Returns a list of all valid moves [(type, r, c), ...] currently available."""
    valid_moves = []
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    h_lines = game_state['horizontal_lines'] # optimization: pass these? No, keep it simple.
    v_lines = game_state['vertical_lines']

    # Check horizontal lines
    for r in range(rows):
        for c in range(cols - 1):
            move = ('h', r, c)
            if move not in h_lines: # Check cache first (minor opt)
                 # Use core logic check for bounds etc.
                 if game_logic.is_valid_line(game_state, 'h', r, c):
                    valid_moves.append(move)

    # Check vertical lines
    for r in range(rows - 1):
        for c in range(cols):
             move = ('v', r, c)
             if move not in v_lines:
                 if game_logic.is_valid_line(game_state, 'v', r, c):
                    valid_moves.append(move)
    return valid_moves

def count_box_sides(game_state, box_r, box_c):
    """Counts the number of existing sides for a box at (box_r, box_c)."""
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    if not (0 <= box_r < rows - 1 and 0 <= box_c < cols - 1):
        # print(f"Warning: count_box_sides called with invalid coords ({box_r}, {box_c})")
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

def completes_box(game_state, line_type, r, c):
    """
    Checks if adding the line (line_type, r, c) would complete any box.
    Uses a temporary simulation without modifying the original state.
    """
    rows = game_state['board_rows']
    cols = game_state['board_cols']

    # --- Simulate adding the line ---
    # Check which boxes this line belongs to and see if they *would* have 4 sides
    boxes_completed = 0
    if line_type == 'h':
        # Box below the line (r, c)
        if r < rows - 1:
            sides = count_box_sides(game_state, r, c)
            if sides == 3: boxes_completed += 1 # Adding this line makes it 4
        # Box above the line (r-1, c)
        if r > 0:
             sides = count_box_sides(game_state, r - 1, c)
             if sides == 3: boxes_completed += 1
    elif line_type == 'v':
        # Box to the right of the line (r, c)
        if c < cols - 1:
             sides = count_box_sides(game_state, r, c)
             if sides == 3: boxes_completed += 1
        # Box to the left of the line (r, c-1)
        if c > 0:
             sides = count_box_sides(game_state, r, c - 1)
             if sides == 3: boxes_completed += 1

    return boxes_completed > 0

def adds_third_line(game_state, line_type, r, c):
    """
    Checks if adding the line (line_type, r, c) adds the 3rd side to any box
    (without completing it - that's handled by completes_box).
    """
    rows = game_state['board_rows']
    cols = game_state['board_cols']

    # Check the box(es) adjacent to this line
    if line_type == 'h':
        # Box below the line (r, c)
        if r < rows - 1:
            if count_box_sides(game_state, r, c) == 2: return True
        # Box above the line (r-1, c)
        if r > 0:
             if count_box_sides(game_state, r - 1, c) == 2: return True
    elif line_type == 'v':
        # Box to the right of the line (r, c)
        if c < cols - 1:
             if count_box_sides(game_state, r, c) == 2: return True
        # Box to the left of the line (r, c-1)
        if c > 0:
             if count_box_sides(game_state, r, c - 1) == 2: return True

    return False

def third_line_sacrifice_count(game_state, line_type, r, c):
    """
    Counts how many boxes this move adds the third line to.
    Used by Minimal Sacrifice policy. Returns 0, 1, or 2.
    """
    count = 0
    rows = game_state['board_rows']
    cols = game_state['board_cols']

    # Check the box(es) adjacent to this line
    if line_type == 'h':
        if r < rows - 1 and count_box_sides(game_state, r, c) == 2:
            count += 1
        if r > 0 and count_box_sides(game_state, r - 1, c) == 2:
            count += 1
    elif line_type == 'v':
        if c < cols - 1 and count_box_sides(game_state, r, c) == 2:
            count += 1
        if c > 0 and count_box_sides(game_state, r, c - 1) == 2:
            count += 1
    return count