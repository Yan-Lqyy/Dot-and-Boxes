# Dots and Boxes: A Python Implementation

Welcome to the Dots and Boxes project! This is a classic pencil-and-paper game brought to life in Python, featuring a text-based interface and a variety of AI opponents with distinct playing styles. Challenge your friends, pit different AI strategies against each other, or see how you fare against the computer!

## The Game: Dots and Boxes

If you're new to Dots and Boxes, here's a quick rundown:

1.  **The Board:** The game starts with an empty rectangular grid of dots.
2.  **The Goal:** The objective is to complete more boxes than your opponent.
3.  **Making a Move:** Players take turns drawing a single horizontal or vertical line between two adjacent, unjoined dots.
4.  **Completing a Box:** If drawing a line completes the fourth side of a 1x1 box, the player who drew that line "claims" the box (usually marked with their initial or color).
5.  **The Extra Turn:** Crucially, whenever a player completes one or more boxes in a single turn, they **must** take another turn immediately. This continues until they draw a line that does not complete any boxes.
6.  **Ending the Game:** The game ends when all possible lines have been drawn and all boxes have been claimed. The player who has claimed more boxes wins.

The strategy often revolves around carefully managing chains of boxes and trying to force your opponent to "open" a chain (draw the third side of a box), allowing you to take the rest.

## Code Structure & Logic

The project is organized into several Python files, each handling a specific aspect of the game:

*   **`game_logic.py`**: The heart of the game. This file defines the rules, manages the game state (board size, lines drawn, box owners, scores, current player), validates moves, checks for box completions, and determines the winner. It doesn't know anything about AI or display.
*   **`display.py`**: Responsible for rendering the current game state to the console. It takes the game state dictionary from `game_logic.py` and prints a readable text-based representation of the board, including dots, player-specific lines (solid vs. dashed), and owned boxes.
*   **`ai_helpers.py`**: Contains common utility functions used by multiple AI policies, such as finding all valid moves, counting the sides of a box, or checking if a move completes a box or adds a third line. This avoids code duplication in the AI files.
*   **`ai_simple_policies.py`**: Implements the basic, non-lookahead AI strategies. These bots react only to the immediate state of the board.
*   **`ai_minimax_ab.py`**: Implements the classic Minimax search algorithm and its optimization, Alpha-Beta Pruning. These AIs look ahead a certain number of moves (depth) to plan their strategy, using a heuristic function to evaluate board states.
*   **`ai_mcts.py`**: Implements the Monte Carlo Tree Search algorithm. This AI uses probabilistic simulation (random playouts) to estimate the value of moves, balancing exploration of new possibilities with exploitation of known good moves.
*   **`ai_player.py`**: Acts as the central registry for all AI policies. It imports the AI functions from the other `ai_*.py` files and creates the `POLICY_MAP` used by `main.py` and `tournament.py` to select and run the desired AI. It also holds shared default parameters like time limits.
*   **`main.py`**: The main executable file to play a single game. It handles game setup (board size, player types - Human or AI), the main game loop, getting input from humans or calling the appropriate AI function, updating the display, and declaring the winner. Includes logic for pausing between moves and displaying AI stop reasons.
*   **`tournament.py`**: A utility script to run batch playoffs between selected AI policies. It simulates many games without display, records the results (wins/losses/ties), and presents a summary table and a plot visualizing the performance of different AIs against each other.

**Core Logic Highlights:**

*   **Game State:** The central `game_state` dictionary in `game_logic.py` holds all information about the current game. This dictionary is passed around between modules.
*   **Line Representation:** Lines are stored in dictionaries (`horizontal_lines`, `vertical_lines`) mapping their coordinate `(r, c)` to the player (1 or 2) who drew them. This allows the display to use player-specific line styles.
*   **AI Modularity:** Each AI strategy is largely self-contained in its own file (or grouped by type), making it easier to understand, modify, or add new AIs without disrupting others. They all receive the `game_state` and return a chosen move (and stop reason).

## Meet the AI Players! (The "Personalities")

This project features a range of AI opponents, from simpletons to sophisticated planners. Think of them as having different personalities:

### The Simpletons (`ai_simple_policies.py`)

These bots live entirely in the present. They don't look ahead or understand complex chain strategy.

*   **"Randy the Random" (`Random`)**: Pure chaos! Randy doesn't think at all; he just picks any legal line available. Completely unpredictable, mostly terrible, but occasionally stumbles into a good move by sheer luck.
*   **"Greta the Greedy" (`Greedy`)**: All about immediate gratification. If Greta sees a line that completes *any* box, she takes it instantly, ignoring any disastrous setup she might be creating for her opponent next turn. If no boxes are available, she panics and plays randomly like Randy.
*   **"Cautious Carl" (`Cautious`)**: The opposite of Greta. Carl is terrified of giving *anything* away. He will *never* place the 3rd line in a box if he can possibly avoid it, even if it means missing a chance to take a box himself. Extremely defensive, often paralyzed by indecision when only "unsafe" moves remain.
*   **"Gary the Pragmatist" (`Greedy+Cautious`)**: A slightly more sensible fellow. Gary follows Greta's "take any box now!" rule first. But if no boxes are available, he listens to Carl and tries to make a "safe" move (one that doesn't place a 3rd line). Only when forced will he make an unsafe move (randomly). Better than Greta or Carl alone, but still fundamentally short-sighted.
*   **"Minnie the Minimizer" (`Minimal Sacrifice`)**: Gary's slightly smarter cousin. Minnie follows the same Greedy > Cautious logic. However, when she *must* make an unsafe move (setting up her opponent), she carefully considers the options and chooses the move that gives away the *fewest* potential boxes (preferring to set up only 1 box instead of 2, if possible). A bit more cunning when backed into a corner.

### The Planners (`ai_minimax_ab.py`, `ai_mcts.py`)

These bots try to anticipate the future, simulating moves and counter-moves.

*   **"Max & Alfie the Calculators" (`Minimax`, `AlphaBeta`)**: These two are deep thinkers (or try to be!). They build a tree of possible future moves, assuming the opponent will always play optimally against them.
    *   **Max (`Minimax`)**: Methodical but slow, explores *every* possibility within its search depth.
    *   **Alfie (`AlphaBeta`)**: Max's clever sibling. Uses Alpha-Beta Pruning to ignore branches of the search tree that clearly won't lead to the best outcome, making him much faster for the same thinking depth.
    *   **How they "think":** They look ahead a fixed `Depth` or for a specific `Time Limit`. When they can't search further, they use a `Heuristic` (judging the board based on score difference and potential chain setups) to guess the outcome. Their weakness is the limit of their lookahead and the accuracy of their heuristic guess. They report if they stopped due to `Depth Limit` or `Time Limit`.
*   **"Monty the Monte Carlo Explorer" (`MCTS`)**: A different kind of thinker. Instead of trying to calculate everything perfectly, Monty plays thousands of super-fast *random* games (simulations or "playouts") in his head for each possible move.
    *   **How he "thinks":** Moves leading to good results in these random playouts are considered promising. He uses a clever formula (UCB1) to balance exploring moves that look good (`Exploitation`) with occasionally trying less-explored moves just in case they're hidden gems (`Exploration`). He doesn't need a complex heuristic like Max & Alfie but relies on the statistical power of many random simulations. His strength depends heavily on the number of `Iterations` run or the `Time Limit` allowed. He reports if he stopped due to `Iteration Limit` or `Time Limit`.

## Running the Game (`main.py`)

To play a game:

1.  Run the script: `python main.py`
2.  Enter the desired board size (number of dots per side, 4-10).
3.  Choose the player type for Player 1 (Human or AI Bot).
4.  If AI Bot, select the desired policy (e.g., "Greedy", "AlphaBeta", "MCTS").
5.  Repeat steps 3-4 for Player 2.
6.  Follow the prompts to make moves (if Human) or watch the AI play! AI moves will include their "Stop Reason" (e.g., why their calculation finished).

## Running Tournaments (`tournament.py`)

To see how different AI strategies perform against each other:

1.  Edit the `tournament.py` file to configure:
    *   `BOARD_SIDE_LENGTH`
    *   `GAMES_PER_MATCHUP` (how many games for P1 vs P2)
    *   `TOURNAMENT_POLICIES` (list of AI policy names to include)
2.  Run the script: `python tournament.py`
3.  The script will simulate all the games (this can take time for search AIs!) and then output:
    *   A table showing the Wins-Losses-Ties for each P1 vs P2 matchup.
    *   A summary of total wins for each policy.
    *   A bar chart visualizing the total wins.

## Future Directions

*   Graphical User Interface (GUI), perhaps as web application.
*   More sophisticated AI heuristics (e.g., explicit chain counting).
*   Advanced AI techniques (e.g., Reinforcement Learning, Neural Networks).
*   Network play to compete against others online.
*   Performance optimizations (e.g., more efficient state representation).
