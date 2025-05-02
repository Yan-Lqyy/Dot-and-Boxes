# display.py
"""
Functions for displaying the Dots and Boxes game state in the console.
"""

def display_board(game_state):
    """
    Prints a text representation of the current game board state.
    'o' represents dots.
    '-' represents horizontal lines.
    '|' represents vertical lines.
    Player number (1 or 2) inside completed boxes.
    """
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    h_lines = game_state['horizontal_lines']
    v_lines = game_state['vertical_lines']
    box_owners = game_state['box_owners']

    print("\nBoard State:")
    for r in range(rows):
        # Print dot row (dots and horizontal lines)
        line1 = ""
        for c in range(cols):
            line1 += "o"
            if c < cols - 1:
                if (r, c) in h_lines:
                    line1 += "---"
                else:
                    line1 += "   "
        print(line1)

        # Print vertical lines and box interiors row (if not the last row)
        if r < rows - 1:
            line2 = ""
            for c in range(cols):
                if (r, c) in v_lines:
                    line2 += "| "
                else:
                    line2 += "  "

                # Check for box owner
                if c < cols - 1:
                    owner = box_owners.get((r, c), 0)
                    if owner != 0:
                        line2 += f"{owner} "
                    else:
                        line2 += "  "
                # Add space if last vertical column has no line
                elif c == cols -1 and (r,c) not in v_lines:
                     line2 += " " # Add trailing space if no vertical line to align

            print(line2.rstrip()) # Use rstrip to remove potential trailing space if no vertical line exists in the last column

    print("-" * (cols * 4 - 3)) # Separator line

def display_scores(game_state):
    """Prints the current scores."""
    print(f"Scores: Player 1: {game_state['scores'][1]} | Player 2: {game_state['scores'][2]}")