# display.py
"""
Functions for displaying the Dots and Boxes game state in the console
with row (letters) and column (numbers) labels.
"""

def display_board(game_state):
    """
    Prints a text representation of the current game board state.
    'o' represents dots.
    '-' represents horizontal lines.
    '|' represents vertical lines.
    Player number (1 or 2) inside completed boxes.
    Includes row letters (A, B, C...) and column numbers (1, 2, 3...).
    """
    rows = game_state['board_rows']
    cols = game_state['board_cols']
    h_lines = game_state['horizontal_lines']
    v_lines = game_state['vertical_lines']
    box_owners = game_state['box_owners']

    # --- Column Headers ---
    col_label_padding = "   " # Space for row labels like "A: "
    header = col_label_padding
    for c in range(cols):
        header += f"{c+1:<4}" # Pad to align with 'o---' pattern
    print(header)

    # --- Board Rows ---
    for r in range(rows):
        row_label = f"{chr(ord('A') + r)}: "

        # Print dot row (dots and horizontal lines)
        line1 = row_label
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
            line2 = col_label_padding # Align under column headers
            for c in range(cols):
                if (r, c) in v_lines:
                    line2 += "| "
                else:
                    line2 += "  "

                # Check for box owner
                if c < cols - 1:
                    owner = box_owners.get((r, c), 0)
                    if owner != 0:
                        line2 += f"{owner} " # Box owner takes 2 spaces (digit + space)
                    else:
                        line2 += "  " # Empty box takes 2 spaces
                # Add trailing space if no vertical line in last column (for alignment)
                # elif c == cols - 1 and (r,c) not in v_lines:
                #     line2 += " " # Ensure alignment if last vertical line is missing - rstrip handles this better

            print(line2.rstrip()) # Use rstrip for cleaner output

    print("-" * len(header)) # Separator line matching header width

def display_scores(game_state):
    """Prints the current scores."""
    print(f"Scores: Player 1: {game_state['scores'][1]} | Player 2: {game_state['scores'][2]}")