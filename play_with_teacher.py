import pygame
import sys
import os

# --- Imports ---
from gomoku_game import GomokuGame

# Try to import the Teacher from your file
try:
    from ai_player_connect4 import TeacherAI_4Row as TeacherAI
except ImportError:
    try:
        from ai_player_connect4 import RuleTeacher as TeacherAI
    except ImportError:
        print("❌ Error: Could not find 'ai_player_connect4.py'")
        sys.exit()

def run_teacher_battle():
    pygame.init()
    
    # 1. Initialize Game
    game = GomokuGame()
    
    # 2. Force 4-in-a-row Rules
    TARGET_WIN = 4
    game.rule_length = TARGET_WIN
    game.board.target_length = TARGET_WIN
    
    pygame.display.set_caption(f"Human vs Teacher (Rule {TARGET_WIN})")

    # 3. Load the TEACHER (Not the Neural Net)
    print("👨‍🏫 Loading Teacher AI...")
    try:
        # The teacher only needs the target length
        game.ai = TeacherAI(target_length=TARGET_WIN)
        game.game_mode = 'ai'
        print("✅ Teacher AI Ready! (Prepare to be blocked)")
    except Exception as e:
        print(f"❌ Error loading Teacher: {e}")
        return

    # 4. Start Game Directly (Bypass Menu)
    print(f"--- 🎮 Game Start! Target: {TARGET_WIN} ---")
    
    # Reset board
    game._reset_game_state()
    
    # Optional: Uncomment to let Teacher go first (White)
    # game.current_player_color = -1 
    # game._trigger_ai_move()
    
    # Start the match loop
    game._play_match()
    
    # 5. Handle End Game (Wait for Q)
    if game.running:
        game._wait_for_menu_input()

    pygame.quit()

if __name__ == "__main__":
    run_teacher_battle()