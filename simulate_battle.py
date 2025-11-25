from gomoku_game import GomokuGame
from rl_ai_player import RL_AIPlayer
import time

def battle(num_games=100):
    p1_wins = 0  # Black (Latest Model)
    p2_wins = 0  # White (5row1 Model)
    draws = 0

    print("--- 正在載入模型 / Loading Models ---")
    try:
        # Player 1 (Black)
        ai_p1 = RL_AIPlayer(model_path="models/gomoku_rl_model_latest.keras")
        # Player 2 (White)
        ai_p2 = RL_AIPlayer(model_path="可以用的model/5row1.keras")
        print("✅ Models loaded successfully!")
    except Exception as e:
        print(f"❌ Error loading models: {e}")
        return

    print(f"--- Starting Battle ({num_games} Games) ---")
    start_time = time.time()

    for i in range(num_games):
        # Initialize game (this opens a window, but we will ignore it)
        game = GomokuGame() 
        
        # We will interact directly with 'game.board' to avoid GUI errors
        board_obj = game.board
        game_over = False
        
        # Start with Player 1 (Black)
        current_color = 1 

        print(f"Playing Game {i+1}/{num_games}...", end="\r")

        while not game_over:
            
            # 1. Get the current grid state directly
            current_grid = board_obj.grid
            
            # 2. Ask AI for a move
            if current_color == 1:
                # Player 1 (Black)
                move = ai_p1.get_move(current_grid, 1)
            else:
                # Player 2 (White)
                move = ai_p2.get_move(current_grid, 2)
            
            # Unpack the move (row, col)
            row, col = move

            # 3. Place the stone directly on the board logic
            # (We skip game.place_stone to avoid Pygame drawing calls)
            if board_obj.is_valid(row, col) and board_obj.is_empty(row, col):
                board_obj.place_stone(row, col, current_color)
            else:
                print(f"\n⚠️ AI tried invalid move: {move}. Ending game.")
                break

            # 4. Check for Win (Must pass the last move coordinates)
            if board_obj.check_win(row, col, current_color):
                if current_color == 1:
                    p1_wins += 1
                else:
                    p2_wins += 1
                game_over = True
            
            # 5. Check for Draw
            elif board_obj.is_full():
                draws += 1
                game_over = True

            # Switch turns
            current_color *= -1

    elapsed_time = time.time() - start_time

    print("\n" + "="*40)
    print("FINAL BATTLE RESULTS")
    print("="*40)
    print(f"Total Games: {num_games}")
    print(f"Time Taken:  {elapsed_time:.2f} seconds")
    print("-" * 20)
    print(f"Player 1 (Latest): {p1_wins} wins ({(p1_wins/num_games)*100:.1f}%)")
    print(f"Player 2 (5row1):  {p2_wins} wins ({(p2_wins/num_games)*100:.1f}%)")
    print(f"Draws:             {draws}")
    print("="*40)

if __name__ == "__main__":
    battle(100)