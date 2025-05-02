# game_logic.py
"""
Core logic for the Dots and Boxes game.
Manages game state, moves, box completion, scoring, and turn management.
"""

def initialize_game(side_length):
    """
    Initializes the game state for a square board.

    Args:
        side_length (int): Number of dots along one side (must be between 4 and 10).

    Returns:
        dict: A dictionary representing the initial game state.
        Raises ValueError if side_length is invalid.
    """
    if not (4 <= side_length <= 10):
        raise ValueError("Board side length (number of dots) must be between 4 and 10.")

    rows = side_length
    cols = side_length

    num_boxes_r = rows - 1
    num_boxes_c = cols - 1
    total_boxes = num_boxes_r * num_boxes_c

    game_state = {
        'board_rows': rows, # Number of dot rows
        'board_cols': cols, # Number of dot columns
        'horizontal_lines': set(), # Stores tuples (r, c) of the top-left dot
        'vertical_lines': set(),   # Stores tuples (r, c) of the top-left dot
        'box_owners': {(r, c): 0 for r in range(num_boxes_r) for c in range(num_boxes_c)}, # 0: no owner, 1: P1, 2: P2
        'scores': {1: 0, 2: 0},
        'current_player': 1,
        'total_boxes': total_boxes,
    }
    return game_state

def _get_max_indices(game_state):
    """Helper to get max row/col indices based on line type."""
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    # Max indices for the *reference dot* of a line
    max_r_h = rows - 1
    max_c_h = cols - 2
    max_r_v = rows - 2
    max_c_v = cols - 1
    return max_r_h, max_c_h, max_r_v, max_c_v

def is_valid_line(game_state, line_type, r, c):
    """Checks if a line is within bounds and not already taken."""
    max_r_h, max_c_h, max_r_v, max_c_v = _get_max_indices(game_state)

    if line_type == 'h': # Horizontal
        # Check bounds for the reference dot (top-left)
        if not (0 <= r <= max_r_h and 0 <= c <= max_c_h):
            # print(f"Debug: H bounds check fail: r={r} (max {max_r_h}), c={c} (max {max_c_h})")
            return False
        # Check if already drawn
        return (r, c) not in game_state['horizontal_lines']
    elif line_type == 'v': # Vertical
        # Check bounds for the reference dot (top-left)
        if not (0 <= r <= max_r_v and 0 <= c <= max_c_v):
            # print(f"Debug: V bounds check fail: r={r} (max {max_r_v}), c={c} (max {max_c_v})")
            return False
        # Check if already drawn
        return (r, c) not in game_state['vertical_lines']
    else:
        return False # Invalid line type

def check_box_completion(game_state, player):
    """
    Checks for newly completed boxes after a line might have been added.
    Updates box_owners and returns the number of boxes completed in this step.

    Args:
        game_state (dict): The current state of the game.
        player (int): The player who potentially completed the box(es).

    Returns:
        int: The number of *newly* completed boxes by this player.
    """
    newly_completed_count = 0
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    h_lines = game_state['horizontal_lines']
    v_lines = game_state['vertical_lines']
    box_owners = game_state['box_owners']

    # Iterate through all possible box top-left corners
    for r in range(rows - 1):
        for c in range(cols - 1):
            # Check if this box is already owned
            if box_owners.get((r, c), 0) == 0: # Use .get for safety, though initialized
                # Check if all four sides are present
                has_top = (r, c) in h_lines
                has_bottom = (r + 1, c) in h_lines
                has_left = (r, c) in v_lines
                has_right = (r, c + 1) in v_lines

                if has_top and has_bottom and has_left and has_right:
                    box_owners[(r, c)] = player
                    newly_completed_count += 1

    return newly_completed_count

def make_move(game_state, line_type, r, c):
    """
    Attempts to draw a line and updates the game state.

    Args:
        game_state (dict): The current state of the game.
        line_type (str): 'h' for horizontal, 'v' for vertical.
        r (int): Row index of the line's reference dot.
        c (int): Column index of the line's reference dot.

    Returns:
        int: Number of boxes completed by this move (0 or more).
             Returns -1 if the move was invalid.
    """
    # Validity check is now primarily handled by the input parsing,
    # but we keep this as a safeguard.
    if not is_valid_line(game_state, line_type, r, c):
        # print(f"Debug: make_move detected invalid line: {line_type}, r={r}, c={c}")
        return -1 # Indicate invalid move

    player = game_state['current_player']

    # Add the line
    if line_type == 'h':
        game_state['horizontal_lines'].add((r, c))
    else: # line_type == 'v'
        game_state['vertical_lines'].add((r, c))

    # Check for completed boxes and update ownership
    boxes_completed_this_turn = check_box_completion(game_state, player)

    # Update score based on *newly* completed boxes
    if boxes_completed_this_turn > 0:
         # Recalculate total score for the player based on owned boxes
         current_player_boxes = sum(1 for owner in game_state['box_owners'].values() if owner == player)
         game_state['scores'][player] = current_player_boxes


    return boxes_completed_this_turn

def switch_player(game_state):
    """Switches the current player."""
    game_state['current_player'] = 3 - game_state['current_player'] # Switches between 1 and 2

def is_game_over(game_state):
    """Checks if all boxes have been claimed."""
    return sum(game_state['scores'].values()) == game_state['total_boxes']

def get_winner(game_state):
    """Determines the winner based on scores. Returns 0 for a tie."""
    score1 = game_state['scores'][1]
    score2 = game_state['scores'][2]
    if score1 > score2:
        return 1
    elif score2 > score1:
        return 2
    else:
        return 0 # Tie