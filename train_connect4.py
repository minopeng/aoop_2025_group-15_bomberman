import os
import sys

# --- CONFIG: HEADLESS MODE ---
os.environ["SDL_VIDEODRIVER"] = "dummy" 
os.environ["CUDA_VISIBLE_DEVICES"] = "-1" 

import numpy as np
import multiprocessing as mp
from random import random
from tqdm import tqdm
import shutil

from gomoku_game import GomokuGame
from rl_ai_player import RL_AIPlayer

try:
    from ai_player_connect4 import TeacherAI_4Row as TeacherAI
except ImportError:
    try:
        from ai_player_connect4 import RuleTeacher as TeacherAI
    except ImportError:
        print("❌ Error: Could not import teacher.")
        sys.exit()

# --- CONFIGURATION ---
MODEL_FILE = "models/connect4_graduation.keras"
TARGET_WIN = 4               
NUM_TOTAL_GAMES = 20000      
GAMES_PER_BATCH = 32         
TRAIN_THRESHOLD = 512        
SAVE_MODEL_EVERY = 50
REPORT_EVERY = 10

# ==========================================
# [EASY MODE ACTIVATED]
# We make the teacher dumb so the student can learn what a "Win" feels like.
# ==========================================
TEACHER_MISTAKE_RATE = 0.2   # Teacher plays randomly 40% of the time!
EPSILON_START = 0.4         # 100% Random start (Fresh brain)
EPSILON_END = 0.01           
EPSILON_DECAY = 0.9995       # Very slow decay to ensure it learns basics
# ==========================================

global_student_ai = None
global_teacher_ai = None

class Quiet:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout

def get_symmetries(board_input, pi_policy):
    state = np.squeeze(board_input)
    pi = pi_policy.reshape(15, 15)
    sym_data = []
    for i in range(4):
        rotated_state = np.rot90(state, i)
        rotated_pi = np.rot90(pi, i)
        sym_data.append((np.expand_dims(rotated_state, 0), rotated_pi.flatten()))
        flipped_state = np.fliplr(rotated_state)
        flipped_pi = np.fliplr(rotated_pi)
        sym_data.append((np.expand_dims(flipped_state, 0), flipped_pi.flatten()))
    return sym_data

# --- IMPROVED REWARD FUNCTION (Now Rewards Blocking!) ---
def calculate_move_quality(board_grid, x, y, color):
    extra_reward = 0
    level = 15
    # Check 4 directions
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dx, dy in directions:
        # 1. Analyze MY line (Attack)
        count_self = 1 
        # ... forward scan ...
        i, j = x + dx, y + dy
        while 0 <= i < level and 0 <= j < level and board_grid[i][j] == color:
            count_self += 1; i += dx; j += dy
        open_1 = (0 <= i < level and 0 <= j < level and board_grid[i][j] == 0)
        # ... backward scan ...
        i, j = x - dx, y - dy
        while 0 <= i < level and 0 <= j < level and board_grid[i][j] == color:
            count_self += 1; i -= dx; j -= dy
        open_2 = (0 <= i < level and 0 <= j < level and board_grid[i][j] == 0)

        # Attack Rewards
        if count_self == 3 and open_1 and open_2: extra_reward += 0.5
        elif count_self == 3 and (open_1 or open_2): extra_reward += 0.3
        elif count_self == 2 and open_1 and open_2: extra_reward += 0.1

        # 2. Analyze OPPONENT line (Defense/Block)
        # We pretend the opponent placed a stone here. If they had a long line,
        # then placing here was a good block!
        opponent_color = -color
        count_opp = 1
        i, j = x + dx, y + dy
        while 0 <= i < level and 0 <= j < level and board_grid[i][j] == opponent_color:
            count_opp += 1; i += dx; j += dy
        
        i, j = x - dx, y - dy
        while 0 <= i < level and 0 <= j < level and board_grid[i][j] == opponent_color:
            count_opp += 1; i -= dx; j -= dy
            
        # Defense Rewards (Blocking)
        if count_opp >= 3: # We blocked a 3 (which would become 4)
            extra_reward += 0.6 # High reward for saving the game!
        elif count_opp == 2:
            extra_reward += 0.2

    return extra_reward

def init_worker():
    global global_student_ai, global_teacher_ai
    with Quiet():
        global_student_ai = RL_AIPlayer()
        global_teacher_ai = TeacherAI(target_length=TARGET_WIN)

def simulation_worker(args):
    weights, epsilon = args
    global global_student_ai, global_teacher_ai
    
    student_ai = global_student_ai
    teacher_ai = global_teacher_ai
    if weights is not None:
        student_ai.model.set_weights(weights)

    with Quiet():
        game = GomokuGame()
        game.board.target_length = TARGET_WIN 

    is_student_black = (random() > 0.5)
    p1 = "student" if is_student_black else "teacher"
    p2 = "teacher" if is_student_black else "student"
        
    current_color = 1
    game_over = False
    game_history = []
    winner_color = 0
    
    while not game_over:
        role = p1 if current_color == 1 else p2
        current_grid = game.board.grid
        state_tensor = student_ai._prepare_input(current_grid, current_color)
        row, col = -1, -1
        move_immediate_reward = 0.0 
        
        if role == "student":
            if random() < epsilon:
                row, col = student_ai._find_random_empty(current_grid)
                if row == -1: row, col = 7, 7
            else:
                row, col = student_ai.get_move(current_grid, current_color)
            
            # Now uses the UPDATED quality check (Attack + Defense)
            move_immediate_reward = calculate_move_quality(current_grid, row, col, current_color)

        else:
            # Teacher makes mistakes now!
            if random() < TEACHER_MISTAKE_RATE:
                row, col = student_ai._find_random_empty(current_grid)
            else:
                row, col = teacher_ai.get_move(current_grid, current_color)
                 
        target_policy = np.zeros(225)
        target_policy[row * 15 + col] = 1.0
        
        game_history.append({
            'state': state_tensor,
            'policy': target_policy,
            'color': current_color,
            'immediate_reward': move_immediate_reward,
            'is_student': (role == "student")
        })
        
        if not game.board.is_valid(row, col):
             winner_color = -current_color
             game_over = True
        else:
            game.board.place_stone(row, col, current_color)
            if game.board.check_win(row, col, current_color):
                winner_color = current_color
                game_over = True
            elif game.board.is_full():
                winner_color = 0
                game_over = True
            
        current_color *= -1
        
    return game_history, winner_color, is_student_black

def train():
    import tensorflow as tf
    gpus = tf.config.list_physical_devices('GPU')
    if gpus:
        try:
            for gpu in gpus:
                tf.config.experimental.set_memory_growth(gpu, True)
        except RuntimeError: pass

    print(f"--- 🐣 Kindergarten Mode (Teacher Mistakes: {TEACHER_MISTAKE_RATE*100}%) ---")
    
    # Always create NEW model for fresh start if requested
    print("🧠 Creating FRESH model (Resetting brain).")
    student_ai = RL_AIPlayer()
    student_ai.model.save(MODEL_FILE)

    num_workers = max(1, mp.cpu_count() - 2)
    print(f"🔥 Using {num_workers} Workers")
    
    memory_buffer = []
    epsilon = EPSILON_START
    games_completed = 0
    batch_count = 0
    
    recent_student_wins = 0
    recent_games_count = 0
    
    with mp.Pool(processes=num_workers, initializer=init_worker) as pool:
        with tqdm(total=NUM_TOTAL_GAMES, unit="game") as pbar:
            while games_completed < NUM_TOTAL_GAMES:
                
                current_weights = student_ai.model.get_weights()
                tasks = [(current_weights, epsilon)] * GAMES_PER_BATCH
                
                results = pool.map(simulation_worker, tasks)
                
                batch_games_count = len(results)
                games_completed += batch_games_count
                pbar.update(batch_games_count)
                
                for history, winner, is_student_black in results:
                    student_color = 1 if is_student_black else -1
                    if winner == student_color:
                        recent_student_wins += 1
                    recent_games_count += 1

                    for step in history:
                        step_reward = 0
                        if winner == step['color']: step_reward = 1.0
                        elif winner == -step['color']: step_reward = -1.0
                        else: step_reward = -0.1
                        
                        # Add immediate reward (Block/Attack) to final result
                        final_val = step_reward + step['immediate_reward']
                        final_val = np.clip(final_val, -1.5, 1.5)
                        
                        aug_data = get_symmetries(step['state'], step['policy'])
                        for s, p in aug_data:
                            memory_buffer.append((s, p, final_val))
                
                if len(memory_buffer) >= TRAIN_THRESHOLD:
                    states = np.vstack([m[0] for m in memory_buffer])
                    policies = np.vstack([m[1] for m in memory_buffer])
                    values = np.array([m[2] for m in memory_buffer])
                    
                    student_ai.model.fit(
                        states, 
                        {'policy_output': policies, 'value_output': values},
                        batch_size=512, 
                        epochs=1, 
                        verbose=0
                    )
                    memory_buffer = [] 
                    if epsilon > EPSILON_END:
                        epsilon *= EPSILON_DECAY
                
                batch_count += 1
                
                if recent_games_count > 0:
                    win_rate = (recent_student_wins / recent_games_count) * 100
                    pbar.set_postfix({'WR': f"{win_rate:.1f}%", 'Eps': f"{epsilon:.2f}"})

                if batch_count % REPORT_EVERY == 0:
                     if recent_games_count > 0:
                        wr = (recent_student_wins / recent_games_count) * 100
                        tqdm.write(f"Wins {recent_student_wins}/{recent_games_count} (WR: {wr:.1f}%)")
                        recent_student_wins = 0
                        recent_games_count = 0

                if batch_count % SAVE_MODEL_EVERY == 0:
                    student_ai.save_model(MODEL_FILE)

    student_ai.save_model(MODEL_FILE)
    print("🎓 Training Complete!")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    train()