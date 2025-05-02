# ai_player.py
"""
Central hub for AI player policies.
Imports policies from other modules and defines the POLICY_MAP.
"""

# Import policy functions from their respective modules
from ai_simple_policies import (get_random_move, get_greedy_box_taker_move,
                                get_cautious_move, get_greedy_cautious_move,
                                get_minimal_sacrifice_move)
from ai_minimax_ab import (get_minimax_move, get_alphabeta_move,
                           DEFAULT_SEARCH_DEPTH as MINIMAX_AB_DEPTH) # Import depth default
from ai_mcts import (get_mcts_move, MCTS_ITERATIONS, MCTS_EXPLORATION) # Import MCTS defaults

# --- Shared Default Constants ---
# Define time limits here if you want them to be easily configurable across search AIs
DEFAULT_TIME_LIMIT = 30.0 # Shared time limit in seconds

# --- Policy Map ---
# Use lambda functions to pass default parameters (depth, time limit, iterations)
POLICY_MAP = {
    # Simple Policies
    "Random": get_random_move,
    "Greedy": get_greedy_box_taker_move,
    "Cautious": get_cautious_move,
    "Greedy+Cautious": get_greedy_cautious_move,
    "Minimal Sacrifice": get_minimal_sacrifice_move,

    # Search Policies (with defaults)
    "Minimax": lambda gs: get_minimax_move(gs,
                                           depth=MINIMAX_AB_DEPTH,
                                           time_limit=DEFAULT_TIME_LIMIT),
    "AlphaBeta": lambda gs: get_alphabeta_move(gs,
                                               depth=MINIMAX_AB_DEPTH,
                                               time_limit=DEFAULT_TIME_LIMIT),
    "MCTS": lambda gs: get_mcts_move(gs,
                                     iterations=MCTS_ITERATIONS,
                                     time_limit=DEFAULT_TIME_LIMIT),
}

# List of available policy names
POLICY_NAMES = list(POLICY_MAP.keys())

# You could also expose the constants if needed elsewhere, e.g., for display
# SEARCH_DEFAULTS = {
#     "MinimaxAB_Depth": MINIMAX_AB_DEPTH,
#     "MCTS_Iterations": MCTS_ITERATIONS,
#     "TimeLimit": DEFAULT_TIME_LIMIT,
#     "MCTS_Exploration": MCTS_EXPLORATION,
# }