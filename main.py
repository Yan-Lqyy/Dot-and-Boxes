# main.py
"""Main execution file for the Dots and Boxes game."""
import game_logic
import display
import string
import time
# Import the central AI hub
import ai_player

# ... (Helpers like _get_col_label, parse_move_input, get_human_player_input, select_player_type remain the same) ...
def _get_col_label(index):
    if 0 <= index < 26: return string.ascii_uppercase[index]
    return '?'
def parse_move_input(input_str, game_state): # ... (implementation as before) ...
    input_str = input_str.strip().upper();
    if len(input_str) < 2: return None
    rows = game_state['board_rows']; cols = game_state['board_cols']; r, c = -1, -1; line_type = None
    try:
        if input_str[0].isdigit() and input_str[-1].isalpha(): # Horiz: 5A
            row_part="".join(filter(str.isdigit, input_str)); col_char="".join(filter(str.isalpha, input_str))
            if len(col_char)!=1 or len(row_part)==0: raise ValueError("Invalid H fmt")
            r=int(row_part); c=string.ascii_uppercase.find(col_char); line_type='h'
            if c == -1: raise ValueError("Invalid col")
            max_r_h, max_c_h, _, _ = game_logic._get_max_indices(game_state)
            if not (0<=r<=max_r_h and 0<=c<=max_c_h): print(f"H OOB ({r}{col_char}). MaxR:{max_r_h}, MaxC:{_get_col_label(max_c_h)}"); return None
        elif input_str[0].isalpha() and input_str[-1].isdigit(): # Vert: A5
            col_char="".join(filter(str.isalpha, input_str)); row_part="".join(filter(str.isdigit, input_str))
            if len(col_char)!=1 or len(row_part)==0: raise ValueError("Invalid V fmt")
            c=string.ascii_uppercase.find(col_char); r=int(row_part); line_type='v'
            if c == -1: raise ValueError("Invalid col")
            _, _, max_r_v, max_c_v = game_logic._get_max_indices(game_state)
            if not (0<=r<=max_r_v and 0<=c<=max_c_v): print(f"V OOB ({col_char}{r}). MaxC:{_get_col_label(max_c_v)}, MaxR:{max_r_v}"); return None
        else: print("Invalid format."); return None
    except (ValueError, IndexError) as e: print(f"Input parse error: {e}"); return None
    if line_type=='h' and (r, c) in game_state['horizontal_lines']: print(f"H Line exists {r}{_get_col_label(c)}"); return None
    if line_type=='v' and (r, c) in game_state['vertical_lines']: print(f"V Line exists {_get_col_label(c)}{r}"); return None
    if not game_logic.is_valid_line(game_state, line_type, r, c): print("Invalid move (logic)."); return None
    return line_type, r, c
def get_human_player_input(current_player, game_state): # ... (implementation as before) ...
    max_r_h, max_c_h, max_r_v, max_c_v = game_logic._get_max_indices(game_state)
    max_col_h_label=_get_col_label(max_c_h); max_col_v_label=_get_col_label(max_c_v)
    while True:
        print(f"\nPlayer {current_player}'s turn (Human). Enter move (e.g., '3{_get_col_label(1)}' H, '{_get_col_label(1)}3' V)")
        print(f"  H:R(0-{max_r_h}),C(A-{max_col_h_label})|V:C(A-{max_col_v_label}),R(0-{max_r_v})")
        move_str = input("Your move: ")
        parsed_move = parse_move_input(move_str, game_state)
        if parsed_move: return parsed_move
def select_player_type(player_num): # ... (implementation as before) ...
     while True:
        print(f"\nSelect Player {player_num} type:\n1: Human\n2: AI Bot")
        choice = input("Enter choice (1 or 2): ")
        if choice == '1': return "Human", None
        elif choice == '2':
            print("\nSelect AI Policy:")
            for i, name in enumerate(ai_player.POLICY_NAMES): print(f"{i+1}: {name}")
            while True:
                policy_choice = input(f"Enter choice (1-{len(ai_player.POLICY_NAMES)}): ")
                try:
                    policy_index = int(policy_choice) - 1
                    if 0 <= policy_index < len(ai_player.POLICY_NAMES): return "Bot", ai_player.POLICY_NAMES[policy_index]
                    else: print("Invalid policy number.")
                except ValueError: print("Invalid input.")
        else: print("Invalid choice.")

if __name__ == "__main__":
    # --- Game Setup ---
    while True:
        try:
            side_len_str = input("Enter board side length (dots, 4 to 10): ")
            game_state = game_logic.initialize_game(int(side_len_str))
            break
        except ValueError as e: print(f"Invalid input: {e}")

    player_config = {}
    p1_type, p1_policy = select_player_type(1); player_config[1] = {"type": p1_type, "policy": p1_policy}
    p2_type, p2_policy = select_player_type(2); player_config[2] = {"type": p2_type, "policy": p2_policy}

    print("\nPlayer Setup Complete.\nGame Started!")

    # --- Main Game Loop ---
    while not game_logic.is_game_over(game_state):
        display.display_board(game_state)
        display.display_scores(game_state)

        player = game_state['current_player']
        config = player_config[player]
        player_type = config["type"]
        policy_name = config["policy"]

        move = None
        stop_reason = "N/A" # Default for humans

        if player_type == "Human":
            # Human input function still returns just the move tuple
            move_tuple = get_human_player_input(player, game_state)
            move = move_tuple # Keep move as the tuple for now
        elif player_type == "Bot":
            print(f"\nPlayer {player}'s turn (Bot: {policy_name}). Thinking...")
            ai_function = ai_player.POLICY_MAP[policy_name]
            start_think_time = time.monotonic()

            # Get the result dictionary from the AI function
            ai_result = ai_function(game_state) # Returns {'move': ..., 'stop_reason': ...}
            think_time = time.monotonic() - start_think_time

            move = ai_result['move'] # Extract the move tuple
            stop_reason = ai_result['stop_reason'] # Extract the reason

            time.sleep(0.05) # Very short delay for visibility

            if move:
                 move_label = f"{move[1]}{_get_col_label(move[2])}" if move[0] == 'h' else f"{_get_col_label(move[2])}{move[1]}"
                 # *** Display the stop reason ***
                 print(f"Bot chose move: {move_label} ({'Hor' if move[0] == 'h' else 'Ver'})")
                 print(f"Stop Reason: {stop_reason} (Think time: {think_time:.3f}s)")
            else:
                 print(f"Bot policy {policy_name} returned no move. Reason: {stop_reason}")
                 # Handle game ending or error based on no move returned
                 if stop_reason == 'No Valid Moves' or stop_reason == 'Game Over':
                      print("Game appears to be over or stalled.")
                 else:
                      print(f"Unexpected error: Bot {policy_name} failed.")
                 break # Exit game loop if bot fails to provide a move

        # --- Process the move ---
        if move is None:
            # Handle cases where input fails or bot returns None move explicitly
            print(f"Error getting move for Player {player} ({player_type}). Stop Reason: {stop_reason}. Skipping turn.")
            if game_logic.is_game_over(game_state): break
            # Avoid infinite loops if a player consistently fails
            # Maybe add a counter? For now, just switch.
            if not game_logic.is_game_over(game_state):
                game_logic.switch_player(game_state)
            continue

        # Unpack the move tuple
        line_type, r, c = move
        boxes_completed = game_logic.make_move(game_state, line_type, r, c)

        if boxes_completed == -1:
            # This indicates an invalid move was somehow generated AFTER validation
            print(f"!!! ERROR: Player {player} ({player_type}) made an invalid move ({move}) that wasn't caught! Skipping turn. !!!")
            game_logic.switch_player(game_state)
            continue

        if boxes_completed > 0:
            print(f"Player {player} ({player_type}) completed {boxes_completed} box(es)! Gets another turn.")
        else:
            game_logic.switch_player(game_state) # Switch player only if no box completed

    # --- Game End ---
    print("\n================ GAME OVER ================")
    # ... (Game end display logic remains the same) ...
    if game_state:
        display.display_board(game_state); display.display_scores(game_state)
        winner = game_logic.get_winner(game_state)
        if winner == 0: print("It's a tie!")
        else: winner_type=player_config[winner]['type']; winner_policy=player_config[winner]['policy']; print(f"Player {winner} ({winner_type}{f' - {winner_policy}' if winner_policy else ''}) wins!")
    else: print("Game ended prematurely.")
    print("==========================================")