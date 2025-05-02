# tournament.py
"""
Runs a batch playoff tournament between selected AI policies
and displays results in a table and plot.
"""

import game_logic
import ai_player # Assuming ai_player.py contains the bot policies and POLICY_MAP
import copy
import time
import pandas as pd
import matplotlib.pyplot as plt
import math # For infinity comparisons in evaluation (needed by bots)

# --- Tournament Configuration ---
BOARD_SIDE_LENGTH = 5  # e.g., 5x5 dots -> 4x4 boxes
GAMES_PER_MATCHUP = 50 # Number of games for each (P1_policy vs P2_policy) pair

# Policies to include in the tournament.
# Choose from the names defined in ai_player.POLICY_NAMES
# Note: Higher depth/time limit policies will be slower.
TOURNAMENT_POLICIES = [
    "Random",
    "Greedy",
    "Cautious",
    "Greedy+Cautious",
    "Minimal Sacrifice",
    # Uncomment search policies as needed, adjust time limits in ai_player.py if too slow
    # "Minimax",
    # "AlphaBeta",
]

# --- Game Simulation Function (similar to main.py loop, but without display) ---

def run_single_game(policy_p1_name, policy_p2_name, board_side_length):
    """
    Runs a single game between two policies and returns the winner (1, 2, or 0 for tie).
    No display output during the game.
    """
    try:
        game_state = game_logic.initialize_game(board_side_length)
    except ValueError as e:
        print(f"Error initializing game for tournament: {e}")
        return -1 # Indicate an error

    policy_p1_func = ai_player.POLICY_MAP.get(policy_p1_name)
    policy_p2_func = ai_player.POLICY_MAP.get(policy_p2_name)

    if not policy_p1_func or not policy_p2_func:
        print(f"Error: Invalid policy name provided: {policy_p1_name} or {policy_p2_name}")
        return -1 # Indicate an error

    while not game_logic.is_game_over(game_state):
        current_player = game_state['current_player']
        current_policy_func = policy_p1_func if current_player == 1 else policy_p2_func

        # Get move from the AI policy
        # Pass game_state to the policy function
        try:
            move = current_policy_func(game_state)
            if move is None:
                # This shouldn't happen if game is not over and valid_moves exist,
                # but as a safeguard:
                print(f"Warning: Policy {current_policy_func.__name__} returned None move when game not over.")
                # Force game end or handle error? For now, treat as loss for this player.
                # A more robust approach might log this and forfeit the game.
                if current_player == 1: return 2 # Player 1 returned None, Player 2 wins
                else: return 1 # Player 2 returned None, Player 1 wins

        except Exception as e:
             print(f"Error during move generation by {current_policy_func.__name__}: {e}")
             # Treat policy error as a loss for that policy
             if current_player == 1: return 2
             else: return 1


        # Make the move
        line_type, r, c = move
        boxes_completed = game_logic.make_move(game_state, line_type, r, c)

        if boxes_completed == -1:
             print(f"Error: Policy {current_policy_func.__name__} generated invalid move {move}. Forfeiting game.")
             # Invalid move generated, forfeit the game
             if current_player == 1: return 2
             else: return 1


        # Switch player only if no boxes were completed
        if boxes_completed == 0:
            game_logic.switch_player(game_state)

    # Game is over, determine winner
    return game_logic.get_winner(game_state)

# --- Tournament Runner ---

def run_tournament(policies, board_side_length, games_per_matchup):
    """
    Runs a round-robin tournament for the given policies.
    """
    results = {} # Store results: { (p1_name, p2_name): {'p1_wins': X, 'p2_wins': Y, 'ties': Z} }

    print(f"Starting tournament with {len(policies)} policies on {board_side_length}x{board_side_length} board.")
    print(f"{games_per_matchup} games per matchup (each player starting). Total games: {len(policies) * len(policies) * games_per_matchup}\n")

    total_games_run = 0
    start_time = time.monotonic()

    for i in range(len(policies)):
        for j in range(len(policies)):
            policy_p1_name = policies[i]
            policy_p2_name = policies[j]

            print(f"Playing {games_per_matchup} games: {policy_p1_name} (P1) vs {policy_p2_name} (P2)...")

            matchup_key = (policy_p1_name, policy_p2_name)
            results[matchup_key] = {'p1_wins': 0, 'p2_wins': 0, 'ties': 0}

            for _ in range(games_per_matchup):
                # Run game with policy_p1 as Player 1 and policy_p2 as Player 2
                winner = run_single_game(policy_p1_name, policy_p2_name, board_side_length)
                total_games_run += 1

                if winner == 1:
                    results[matchup_key]['p1_wins'] += 1
                elif winner == 2:
                    results[matchup_key]['p2_wins'] += 1
                elif winner == 0:
                    results[matchup_key]['ties'] += 1
                else: # Error case (-1)
                    print(f"Skipping game due to error in matchup {policy_p1_name} vs {policy_p2_name}")


    end_time = time.monotonic()
    print(f"\nTournament finished in {end_time - start_time:.2f} seconds.")
    print(f"Total games simulated: {total_games_run}")

    return results

# --- Display Results ---

def display_table(results, policies):
    """
    Displays tournament results in a formatted table.
    """
    # Create a pandas DataFrame for easier table display
    # Index: Policy playing as P1
    # Columns: Policy playing as P2
    # Values: Result string (e.g., "Wins-Losses-Ties")
    table_data = {}
    for p1_name in policies:
        table_data[p1_name] = {}
        for p2_name in policies:
            if (p1_name, p2_name) in results:
                res = results[(p1_name, p2_name)]
                table_data[p1_name][p2_name] = f"{res['p1_wins']}-{res['p2_wins']}-{res['ties']}"
            else:
                table_data[p1_name][p2_name] = "-" # Should not happen if all matchups played

    df = pd.DataFrame(table_data)

    print("\n--- Tournament Results Table (P1 Wins - P2 Wins - Ties) ---")
    print(df)
    print("-" * 60)

    # Also show total wins for each policy
    total_wins = {policy: 0 for policy in policies}
    total_games_played = {policy: 0 for policy in policies}

    for (p1_name, p2_name), res in results.items():
         total_wins[p1_name] += res['p1_wins']
         total_wins[p2_name] += res['p2_wins'] # Wins for P2 in this matchup are wins for policy_p2_name

         total_games_played[p1_name] += res['p1_wins'] + res['p2_wins'] + res['ties']
         total_games_played[p2_name] += res['p1_wins'] + res['p2_wins'] + res['ties']

    # Note: total_games_played will count each game twice (once for P1, once for P2)
    # This is fine if we just want total wins. If we want win%, need total games per policy.
    # The simpler approach is total wins as P1 + total wins as P2

    print("\n--- Total Wins per Policy (as Player 1 + as Player 2) ---")
    total_wins_series = pd.Series(total_wins).sort_values(ascending=False)
    print(total_wins_series)
    print("-" * 60)


def display_plot(results, policies):
    """
    Displays tournament results using matplotlib (e.g., total wins).
    """
    total_wins = {policy: 0 for policy in policies}

    for (p1_name, p2_name), res in results.items():
         total_wins[p1_name] += res['p1_wins']
         total_wins[p2_name] += res['p2_wins']

    policy_names = list(total_wins.keys())
    win_counts = list(total_wins.values())

    # Sort for better visualization
    sorted_indices = sorted(range(len(win_counts)), key=lambda k: win_counts[k], reverse=True)
    sorted_policy_names = [policy_names[i] for i in sorted_indices]
    sorted_win_counts = [win_counts[i] for i in sorted_indices]


    plt.figure(figsize=(10, 6))
    plt.bar(sorted_policy_names, sorted_win_counts, color='skyblue')
    plt.xlabel("AI Policy")
    plt.ylabel("Total Wins (as P1 + as P2)")
    plt.title("Tournament Results: Total Wins per AI Policy")
    plt.xticks(rotation=45, ha='right') # Rotate labels if they overlap
    plt.tight_layout() # Adjust layout to prevent labels overlapping
    plt.show()


# --- Main Execution ---
if __name__ == "__main__":
    # Validate requested policies exist
    invalid_policies = [p for p in TOURNAMENT_POLICIES if p not in ai_player.POLICY_MAP]
    if invalid_policies:
        print(f"Error: The following policies are not found in ai_player.POLICY_MAP: {invalid_policies}")
        print(f"Available policies are: {ai_player.POLICY_NAMES}")
    else:
        tournament_results = run_tournament(TOURNAMENT_POLICIES, BOARD_SIDE_LENGTH, GAMES_PER_MATCHUP)

        if tournament_results: # Check if any games were successfully run
             display_table(tournament_results, TOURNAMENT_POLICIES)
             display_plot(tournament_results, TOURNAMENT_POLICIES)