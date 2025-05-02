# display.py
"""
Functions for displaying the Dots and Boxes game state in the console.
"""
import string

def _get_col_label(index):
    """Returns the column label (A, B, ...) for a given index."""
    if index < 26:
        return string.ascii_uppercase[index]
    else:
        # Handle more than 26 columns if needed, though current limit is 10 dots (J)
        return "?" # Placeholder for columns beyond Z

def display_board(game_state):
    """
    Prints a text representation of the current game board state with row/col labels.
    'o' represents dots.
    '-' represents horizontal lines.
    '|' represents vertical lines.
    Player number (1 or 2) inside completed boxes.
    Row numbers on the left, Column letters on top.
    """
    rows = game_state['board_rows']
    cols = game_state['board_cols']
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
        line1 = f"{r:<2d} " # Row number, left-aligned in 2 spaces
        for c in range(cols):
            line1 += "o" # Print dot
            if c < cols - 1: # Check if a horizontal line can exist to the right
                if (r, c) in h_lines:
                    line1 += "---" # Drawn line
                else:
                    line1 += "   " # Empty space for line
        print(line1)

        # Print vertical lines and box interiors row (if not the last dot row)
        if r < rows - 1:
            line2 = "   " # Space for row numbers
            for c in range(cols):
                # Check for vertical line below the current dot
                if (r, c) in v_lines:
                    line2 += "| " # Drawn vertical line
                else:
                    line2 += "  " # Empty space for vertical line

                # Check for box owner to the right of the vertical line space
                if c < cols - 1:
                    owner = box_owners.get((r, c), 0) # (r,c) is the top-left of the box
                    if owner != 0:
                        line2 += f"{owner} " # Show owner (1 or 2)
                    else:
                        line2 += "  " # Empty box interior
                # Add space if last vertical column has no line, ensuring alignment
                elif c == cols - 1 and (r, c) not in v_lines:
                    line2 += " "

            print(line2.rstrip()) # Remove potential trailing space

    # Optional: Bottom separator line (adjust width)
    # print("   " + "-" * (cols * 4 - 1))

def display_scores(game_state):
    """Prints the current scores."""
    print(f"\nScores: Player 1: {game_state['scores'][1]} | Player 2: {game_state['scores'][2]}")