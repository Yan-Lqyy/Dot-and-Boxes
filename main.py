# main.py
"""
Main execution file for the Dots and Boxes game.
Handles game setup, the main game loop, player input (Human/Bot), and game end conditions.
"""

import game_logic
import display
import string
import time # Optional: To add slight delay for bot moves
import ai_player # Import the new AI logic

# Helper function (from previous version, slightly adapted for clarity)
def _get_col_label(index):
    if 0 <= index < 26:
        return string.ascii_uppercase[index]
    return '?'

# Input parsing function (from previous version)
def parse_move_input(input_str, game_state):
    """
    Parses the player's single-string input (e.g., "5A" or "A5")
    into line type, row, and column index. Returns (line_type, r, c) or None.
    """
    input_str = input_str.strip().upper()
    if len(input_str) < 2:
        print("Invalid input: Too short. Use format like '5A' (horizontal) or 'A5' (vertical).")
        return None

    rows = game_state['board_rows']
    cols = game_state['board_cols']

    r, c = -1, -1
    line_type = None

    # Try Horizontal format: Digit(s)Letter (e.g., "5A")
    if input_str[0].isdigit() and input_str[-1].isalpha():
        try:
            row_part = ""
            col_char = ''
            for i, char in enumerate(input_str):
                if char.isdigit():
                    row_part += char
                elif char.isalpha() and i == len(input_str) - 1:
                    col_char = char
                    break
                else: raise ValueError("Invalid format")
            if not col_char: raise ValueError("Missing column letter")

            r = int(row_part)
            c = string.ascii_uppercase.find(col_char)
            if c == -1: raise ValueError("Invalid column letter")
            line_type = 'h'

            max_r_h, max_c_h, _, _ = game_logic._get_max_indices(game_state)
            if not (0 <= r <= max_r_h and 0 <= c <= max_c_h):
                 print(f"Invalid input: Horizontal line coordinates ({r}{col_char}) out of bounds.")
                 print(f"   Valid row: 0-{max_r_h}. Valid col: A-{_get_col_label(max_c_h)}.")
                 return None
        except (ValueError, IndexError) as e:
            # print(f"Debug H parse error: {e}") # Optional debug
            print("Invalid input format for horizontal line (e.g., '5A').")
            return None

    # Try Vertical format: LetterDigit(s) (e.g., "A5")
    elif input_str[0].isalpha() and input_str[-1].isdigit():
         try:
            col_char = input_str[0]
            if not col_char.isalpha() or len(input_str) < 2 or not input_str[1:].isdigit():
                 raise ValueError("Invalid format")

            c = string.ascii_uppercase.find(col_char)
            if c == -1: raise ValueError("Invalid column letter")
            r = int(input_str[1:])
            line_type = 'v'

            _, _, max_r_v, max_c_v = game_logic._get_max_indices(game_state)
            if not (0 <= r <= max_r_v and 0 <= c <= max_c_v):
                 print(f"Invalid input: Vertical line coordinates ({col_char}{r}) out of bounds.")
                 print(f"   Valid col: A-{_get_col_label(max_c_v)}. Valid row: 0-{max_r_v}.")
                 return None
         except (ValueError, IndexError) as e:
            # print(f"Debug V parse error: {e}") # Optional debug
            print("Invalid input format for vertical line (e.g., 'A5').")
            return None
    else:
        print("Invalid input format. Use RowNum+ColLetter (e.g., '5A') for horizontal or ColLetter+RowNum (e.g., 'A5') for vertical.")
        return None

    # Check if line already exists (redundant with is_valid_line but good for early user feedback)
    if line_type == 'h' and (r, c) in game_state['horizontal_lines']:
        print(f"Invalid move: Horizontal line at {r}{_get_col_label(c)} already exists.")
        return None
    if line_type == 'v' and (r, c) in game_state['vertical_lines']:
         print(f"Invalid move: Vertical line at {_get_col_label(c)}{r} already exists.")
         return None

    # Final check with core logic function before returning parsed value
    if not game_logic.is_valid_line(game_state, line_type, r, c):
         print("Invalid move: Line is out of bounds or already taken (logic check).")
         return None

    return line_type, r, c


# Human input function (modified slightly for clarity)
def get_human_player_input(current_player, game_state):
    """Gets and validates move input from a human player."""
    max_r_h, max_c_h, max_r_v, max_c_v = game_logic._get_max_indices(game_state)
    max_col_h_label = _get_col_label(max_c_h)
    max_col_v_label = _get_col_label(max_c_v)

    while True:
        print(f"\nPlayer {current_player}'s turn (Human).")
        print(f"Enter move (e.g., '3{_get_col_label(1)}' for horizontal, '{_get_col_label(1)}3' for vertical)")
        print(f"  H range: R(0-{max_r_h}), C(A-{max_col_h_label}) | V range: C(A-{max_col_v_label}), R(0-{max_r_v})")

        move_str = input("Your move: ")
        parsed_move = parse_move_input(move_str, game_state)

        if parsed_move:
            return parsed_move # Returns (line_type, r, c)
        # else: Error message was printed by parse_move_input

# --- Player Type Selection ---
def select_player_type(player_num):
    """Asks user to select Human or Bot type for a player."""
    while True:
        print(f"\nSelect Player {player_num} type:")
        print("1: Human")
        print("2: AI Bot")
        choice = input("Enter choice (1 or 2): ")
        if choice == '1':
            return "Human", None
        elif choice == '2':
            print("\nSelect AI Policy:")
            for i, name in enumerate(ai_player.POLICY_NAMES):
                print(f"{i+1}: {name}")
            while True:
                policy_choice = input(f"Enter choice (1-{len(ai_player.POLICY_NAMES)}): ")
                try:
                    policy_index = int(policy_choice) - 1
                    if 0 <= policy_index < len(ai_player.POLICY_NAMES):
                        policy_name = ai_player.POLICY_NAMES[policy_index]
                        return "Bot", policy_name
                    else:
                        print("Invalid policy number.")
                except ValueError:
                    print("Invalid input. Please enter a number.")
        else:
            print("Invalid choice. Please enter 1 or 2.")


if __name__ == "__main__":
    # --- Game Setup ---
    while True:
        try:
            side_len_str = input("Enter board side length (number of dots, 4 to 10): ")
            side_length = int(side_len_str)
            game_state = game_logic.initialize_game(side_length) # Raises ValueError if invalid
            break
        except ValueError as e:
            print(f"Invalid input: {e}")

    # --- Select Player Types ---
    player_config = {} # Stores type and policy for each player
    p1_type, p1_policy = select_player_type(1)
    player_config[1] = {"type": p1_type, "policy": p1_policy}

    p2_type, p2_policy = select_player_type(2)
    player_config[2] = {"type": p2_type, "policy": p2_policy}

    print("\nPlayer Setup:")
    print(f"Player 1: {player_config[1]['type']}" + (f" ({player_config[1]['policy']})" if player_config[1]['policy'] else ""))
    print(f"Player 2: {player_config[2]['type']}" + (f" ({player_config[2]['policy']})" if player_config[2]['policy'] else ""))

    print("\nGame Started!")
    # --- Main Game Loop ---
    while not game_logic.is_game_over(game_state):
        display.display_board(game_state)
        display.display_scores(game_state)

        player = game_state['current_player']
        config = player_config[player]
        player_type = config["type"]
        policy_name = config["policy"] # None if Human

        move = None
        if player_type == "Human":
            move = get_human_player_input(player, game_state)
        elif player_type == "Bot":
            print(f"\nPlayer {player}'s turn (Bot: {policy_name}). Thinking...")
            ai_function = ai_player.POLICY_MAP[policy_name]
            move = ai_function(game_state)
            # Optional: Add a small delay to make bot moves visible
            time.sleep(0.5)
            if move:
                 move_label = f"{move[1]}{_get_col_label(move[2])}" if move[0] == 'h' else f"{_get_col_label(move[2])}{move[1]}"
                 print(f"Bot chose move: {move_label} ({'Horizontal' if move[0] == 'h' else 'Vertical'})")
            else:
                 print("Bot could not find a move (Error or Game End).")
                 # This should ideally not happen if is_game_over is checked first
                 break


        if move is None:
            # Handle cases where input fails or bot returns None unexpectedly
            print("Error getting move. Skipping turn (or end game).")
            # Decide how to handle this - maybe break, maybe switch player
            if game_logic.is_game_over(game_state): break # Check again if game ended
            game_logic.switch_player(game_state) # Simple fallback: switch player
            continue

        # --- Make the Move ---
        line_type, r, c = move
        boxes_completed = game_logic.make_move(game_state, line_type, r, c)

        if boxes_completed == -1:
            # Should not happen if input/bot logic is correct & provides valid moves
            print(f"!!! ERROR: Player {player} ({player_type}) provided an invalid move ({move}) that passed initial checks! Skipping turn. !!!")
            game_logic.switch_player(game_state) # Switch player to avoid loops
            continue

        # --- Post-Move Logic ---
        if boxes_completed > 0:
            print(f"Player {player} ({player_type}) completed {boxes_completed} box(es)! They get another turn.")
            # Player doesn't switch, loop continues with the same player
        else:
            # Switch to the other player if no box was completed
            game_logic.switch_player(game_state)

    # --- Game End ---
    print("\n================ GAME OVER ================")
    if game_state: # Ensure game_state was initialized
        display.display_board(game_state) # Show final board
        display.display_scores(game_state)
        winner = game_logic.get_winner(game_state)
        if winner == 0:
            print("It's a tie!")
        else:
            winner_type = player_config[winner]['type']
            winner_policy = player_config[winner]['policy']
            print(f"Player {winner} ({winner_type}{f' - {winner_policy}' if winner_policy else ''}) wins!")
    else:
        print("Game ended prematurely.")
    print("==========================================")