# main.py
"""
Main execution file for the Dots and Boxes game.
Handles game setup, the main game loop, player input, and game end conditions.
"""

import game_logic
import display

def get_player_input(current_player):
    """Gets and validates move input from the current player."""
    while True:
        try:
            print(f"\nPlayer {current_player}'s turn.")
            line_type = input("Enter line type ('h' for horizontal, 'v' for vertical): ").lower()
            if line_type not in ['h', 'v']:
                print("Invalid line type. Please enter 'h' or 'v'.")
                continue

            r_str = input(f"Enter row index (0 to {game_state['board_rows'] - (1 if line_type == 'h' else 2)}): ")
            c_str = input(f"Enter column index (0 to {game_state['board_cols'] - (2 if line_type == 'h' else 1)}): ")

            r = int(r_str)
            c = int(c_str)

            return line_type, r, c

        except ValueError:
            print("Invalid input. Please enter numbers for row and column.")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    # --- Game Setup ---
    while True:
        try:
            board_rows = int(input("Enter number of rows of DOTS (e.g., 3 for a 2x2 box grid): "))
            board_cols = int(input("Enter number of columns of DOTS (e.g., 3 for a 2x2 box grid): "))
            if board_rows >= 2 and board_cols >= 2:
                break
            else:
                print("Board must have at least 2 rows and 2 columns of dots.")
        except ValueError:
            print("Invalid input. Please enter numbers.")

    game_state = game_logic.initialize_game(board_rows, board_cols)
    print("\nGame Started!")

    # --- Main Game Loop ---
    while not game_logic.is_game_over(game_state):
        display.display_board(game_state)
        display.display_scores(game_state)

        player = game_state['current_player']

        # --- Get Valid Move ---
        # In the future, you could replace get_player_input with get_ai_move
        # based on whether the current player is human or AI.
        while True:
            line_type, r, c = get_player_input(player)
            boxes_completed = game_logic.make_move(game_state, line_type, r, c)

            if boxes_completed == -1:
                print("!!! Invalid move. The line is out of bounds or already taken. Try again. !!!")
            else:
                break # Valid move was made

        # --- Post-Move Logic ---
        if boxes_completed > 0:
            print(f"Player {player} completed {boxes_completed} box(es)! They get another turn.")
            # Player doesn't switch, loop continues with the same player
        else:
            # Switch to the other player if no box was completed
            game_logic.switch_player(game_state)

    # --- Game End ---
    print("\n================ GAME OVER ================")
    display.display_board(game_state)
    display.display_scores(game_state)

    winner = game_logic.get_winner(game_state)
    if winner == 0:
        print("It's a tie!")
    else:
        print(f"Player {winner} wins!")
    print("==========================================")