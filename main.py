# main.py
"""
Main execution file for the Dots and Boxes game.
Handles game setup, the main game loop, player input, and game end conditions.
"""

import game_logic
import display
import string # Needed for input parsing

def parse_move_input(input_str, game_state):
    """
    Parses the player's single-string input (e.g., "5A" or "A5")
    into line type, row, and column index.

    Args:
        input_str (str): The raw user input string.
        game_state (dict): The current game state (needed for bounds).

    Returns:
        tuple: (line_type, r, c) if valid, otherwise None.
               line_type is 'h' or 'v'.
               r, c are zero-based integer indices.
    """
    input_str = input_str.strip().upper()
    if len(input_str) < 2:
        print("Invalid input: Too short. Use format like '5A' (horizontal) or 'A5' (vertical).")
        return None

    rows = game_state['board_rows']
    cols = game_state['board_cols']
    max_row_idx = rows - 1
    max_col_idx = cols - 1

    r, c = -1, -1
    line_type = None

    # Try Horizontal format: Digit(s)Letter (e.g., "5A")
    if input_str[0].isdigit() and input_str[-1].isalpha():
        try:
            # Handle potential multi-digit rows (though max is 9 here)
            row_part = ""
            col_char = ''
            for i, char in enumerate(input_str):
                if char.isdigit():
                    row_part += char
                elif char.isalpha() and i == len(input_str) - 1: # Must be the last char
                    col_char = char
                    break # Found the letter part
                else:
                    raise ValueError("Invalid format") # Non-digit before letter or multiple letters

            if not col_char: raise ValueError("Missing column letter")

            r = int(row_part)
            c = string.ascii_uppercase.find(col_char)
            line_type = 'h'

            # Validate indices for horizontal line
            max_r_h, max_c_h, _, _ = game_logic._get_max_indices(game_state)
            if not (0 <= r <= max_r_h and 0 <= c <= max_c_h):
                 print(f"Invalid input: Horizontal line coordinates ({r}{col_char}) out of bounds.")
                 print(f"   Valid row index: 0 to {max_r_h}. Valid column index: A to {_get_col_label(max_c_h)}.")
                 return None

        except (ValueError, IndexError):
            print("Invalid input format for horizontal line (e.g., '5A').")
            return None

    # Try Vertical format: LetterDigit(s) (e.g., "A5")
    elif input_str[0].isalpha() and input_str[-1].isdigit():
         try:
            col_char = input_str[0]
            if not col_char.isalpha() or len(input_str) < 2 or not input_str[1:].isdigit():
                 raise ValueError("Invalid format")

            c = string.ascii_uppercase.find(col_char)
            r = int(input_str[1:])
            line_type = 'v'

            # Validate indices for vertical line
            _, _, max_r_v, max_c_v = game_logic._get_max_indices(game_state)
            if not (0 <= r <= max_r_v and 0 <= c <= max_c_v):
                 print(f"Invalid input: Vertical line coordinates ({col_char}{r}) out of bounds.")
                 print(f"   Valid column index: A to {_get_col_label(max_c_v)}. Valid row index: 0 to {max_r_v}.")
                 return None

         except (ValueError, IndexError):
            print("Invalid input format for vertical line (e.g., 'A5').")
            return None

    else:
        print("Invalid input format. Use RowNum+ColLetter (e.g., '5A') for horizontal or ColLetter+RowNum (e.g., 'A5') for vertical.")
        return None

    # Final check if the specific line is already taken
    if line_type == 'h' and (r, c) in game_state['horizontal_lines']:
        print(f"Invalid move: Horizontal line at {r}{_get_col_label(c)} already exists.")
        return None
    if line_type == 'v' and (r, c) in game_state['vertical_lines']:
         print(f"Invalid move: Vertical line at {_get_col_label(c)}{r} already exists.")
         return None

    return line_type, r, c


# Helper to use in parse_move_input for error messages
def _get_col_label(index):
    if 0 <= index < 26:
        return string.ascii_uppercase[index]
    return '?'


def get_player_input(current_player, game_state):
    """Gets and validates move input from the current player using single string format."""
    max_r_h, max_c_h, max_r_v, max_c_v = game_logic._get_max_indices(game_state)
    max_col_h_label = _get_col_label(max_c_h)
    max_col_v_label = _get_col_label(max_c_v)

    while True:
        print(f"\nPlayer {current_player}'s turn.")
        print(f"Enter move (e.g., '3B' for horizontal line at Row 3, Col B; 'B3' for vertical line at Col B, Row 3)")
        # Provide range guidance based on game size
        print(f"  Horizontal valid range: Row (0-{max_r_h}), Col (A-{max_col_h_label}) -> e.g., {max_r_h}{max_col_h_label}")
        print(f"  Vertical valid range: Col (A-{max_col_v_label}), Row (0-{max_r_v}) -> e.g., {max_col_v_label}{max_r_v}")

        move_str = input("Your move: ")
        parsed_move = parse_move_input(move_str, game_state)

        if parsed_move:
            line_type, r, c = parsed_move
            # Double check with the core logic function (optional but safe)
            if game_logic.is_valid_line(game_state, line_type, r, c):
                 return line_type, r, c
            else:
                 # This case should ideally be caught by parse_move_input already
                 print("!!! Internal Check Failed: Move is invalid or line already taken. Please try again. !!!")
        # else: Error message was already printed by parse_move_input


if __name__ == "__main__":
    # --- Game Setup ---
    while True:
        try:
            # Ask for side length of dots grid
            side_len_str = input("Enter board side length (number of dots, 4 to 10): ")
            side_length = int(side_len_str)
            # Validation is now inside initialize_game, which will raise ValueError
            game_state = game_logic.initialize_game(side_length)
            break # Exit loop if initialization is successful
        except ValueError as e:
            print(f"Invalid input: {e}") # Print the error from initialize_game

    print("\nGame Started!")

    # --- Main Game Loop ---
    while not game_logic.is_game_over(game_state):
        display.display_board(game_state)
        display.display_scores(game_state)

        player = game_state['current_player']

        # --- Get Valid Move (using the new input function) ---
        line_type, r, c = get_player_input(player, game_state)

        # --- Make the Move ---
        # We trust the input function validated the move,
        # make_move primarily adds the line and checks for boxes
        boxes_completed = game_logic.make_move(game_state, line_type, r, c)

        if boxes_completed == -1:
            # This should ideally not happen if get_player_input works correctly,
            # but indicates an unexpected issue.
            print("!!! ERROR: Move failed unexpectedly after validation. Please report this. !!!")
            # Maybe force player switch or handle differently? For now, just report.
            game_logic.switch_player(game_state) # Prevent potential infinite loop
            continue

        # --- Post-Move Logic ---
        if boxes_completed > 0:
            print(f"Player {player} completed {boxes_completed} box(es)! They get another turn.")
            # Player doesn't switch, loop continues with the same player
        else:
            # Switch to the other player if no box was completed
            game_logic.switch_player(game_state)

    # --- Game End ---
    print("\n================ GAME OVER ================")
    display.display_board(game_state) # Show final board
    display.display_scores(game_state)

    winner = game_logic.get_winner(game_state)
    if winner == 0:
        print("It's a tie!")
    else:
        print(f"Player {winner} wins!")
    print("==========================================")