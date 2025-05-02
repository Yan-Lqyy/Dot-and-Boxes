# display.py
"""Functions for displaying the Dots and Boxes game state."""
import string

# Define line styles for players
H_LINE_STYLE = {1: "===", 2: "---"} # Player 1: double, Player 2: single dash
V_LINE_STYLE = {1: "‖", 2: "|"}   # Player 1: double, Player 2: single pipe
EMPTY_H_LINE = "   "
EMPTY_V_SPACE = " " # Space where a vertical line could be

def _get_col_label(index):
    """Returns column label (A, B, ...)."""
    if 0 <= index < 26: return string.ascii_uppercase[index]
    return '?'

def display_board(game_state):
    """Prints board state with row/col labels and player-specific lines."""
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    # Access the dictionaries
    h_lines = game_state['horizontal_lines']
    v_lines = game_state['vertical_lines']
    box_owners = game_state['box_owners']

    print("\nBoard State:")

    # --- Print Column Headers ---
    header = "   " # Space for row numbers
    for c in range(cols):
        header += f" {_get_col_label(c)}  "
    print(header)

    # --- Print Board Rows ---
    for r in range(rows):
        # Print dot row (dots and horizontal lines)
        line1 = f"{r:<2d} " # Row number
        for c in range(cols):
            line1 += "o" # Print dot
            if c < cols - 1:
                # *** CHANGED: Check owner and draw style ***
                owner = h_lines.get((r, c)) # Returns None if line doesn't exist
                line_style = H_LINE_STYLE.get(owner, EMPTY_H_LINE) # Get style or empty
                line1 += line_style
        print(line1)

        # Print vertical lines and box interiors row (if not the last dot row)
        if r < rows - 1:
            line2 = "   " # Space for row numbers
            for c in range(cols):
                 # *** CHANGED: Check owner and draw style ***
                owner = v_lines.get((r, c)) # Returns None if line doesn't exist
                line_style = V_LINE_STYLE.get(owner, EMPTY_V_SPACE) # Get style or empty
                line2 += line_style

                # Box interior (add spacing based on vertical line width)
                # Check for box owner to the right of the vertical line space
                if c < cols - 1:
                    box_owner = box_owners.get((r, c), 0) # (r,c) is the top-left
                    box_char = f" {box_owner} " if box_owner != 0 else "   " # Pad box number
                    line2 += box_char
                else:
                     # Add trailing space if no line to keep alignment consistent
                     line2 += " " if owner is None else ""


            print(line2.rstrip()) # Remove potential excess trailing space

def display_scores(game_state):
    """Prints the current scores."""
    print(f"\nScores: Player 1: {game_state['scores'][1]} | Player 2: {game_state['scores'][2]}")