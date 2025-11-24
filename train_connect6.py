# train_connect6.py
# Dedicated training script for 6-in-a-row (Connect6)

import os
os.environ["CUDA_VISIBLE_DEVICES"] = "-1" 

import numpy as np
import multiprocessing as mp
from random import random
from tqdm import tqdm 

from game_board import GameBoard
from ai_player import AIPlayer
from rl_ai_player import RL_AIPlayer

# --- Settings ---
NUM_TOTAL_GAMES = 20000
GAMES_PER_BATCH = 32        
TRAIN_THRESHOLD = 512
SAVE_MODEL_EVERY = 50       
REPORT_EVERY = 10           
MODEL_SAVE_PATH = "models/"
TARGET_RULE = 6  # [IMPORTANT] Training for Connect 6

TEACHER_MISTAKE_RATE = 0.4 
EPSILON_START = 0.3  
EPSILON_END = 0.01
EPSILON_DECAY = 0.995

os.makedirs(MODEL_SAVE_PATH, exist_ok=True)

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

# --- [MODIFIED] Heuristic for 6-in-a-Row ---
def calculate_move_quality(board_grid, x, y, color):
    extra_reward = 0
    level = 15
    directions = [(0, 1), (1, 0), (1, 1), (1, -1)]
    
    for dx, dy in directions:
        count = 1 
        i, j = x + dx, y + dy
        while 0 <= i < level and 0 <= j < level and board_grid[i][j] == color:
            count += 1; i += dx; j += dy
        open_end_1 = (0 <= i < level and 0 <= j < level and board_grid[i][j] == 0)
        
        i, j = x - dx, y - dy
        while 0 <= i < level and 0 <= j < level and board_grid[i][j] == color:
            count += 1; i -= dx; j -= dy
        open_end_2 = (0 <= i < level and 0 <= j < level and board_grid[i][j] == 0)
        
        # [REWARDS FOR CONNECT 6]
        if count == 5 and open_end_1 and open_end_2: extra_reward += 0.6
        elif count == 5 and (open_end_1 or open_end_2): extra_reward += 0.4
        elif count == 4 and open_end_1 and open_end_2: extra_reward += 0.3
        elif count == 3 and open_end_1 and open_end_2: extra_reward += 0.05
        
    return extra_reward

def simulation_worker(args):
    weights, epsilon = args
    import os
    os.environ["CUDA_VISIBLE_DEVICES"] = "-1"
    import tensorflow as tf
    
    # [IMPORTANT] Initialize Board and Teacher with RULE = 6
    board = GameBoard(target_length=TARGET_RULE)
    teacher_ai = AIPlayer(target_length=TARGET_RULE)
    student_ai = RL_AIPlayer() 
    student_ai.model.set_weights(weights)
    
    is_observation_mode = (random() < 0.2) 
    if is_observation_mode: p1, p2 = "teacher", "teacher"
    else: p1, p2 = "student", "teacher"
        
    current_color = 1
    last_xy = (-1, -1)
    game_over = False
    game_history = []
    winner_color = 0
    
    while not game_over:
        role = p1 if current_color == 1 else p2
        state_tensor = student_ai._prepare_input(board.grid, current_color)
        ax, ay = -1, -1
        move_immediate_reward = 0.0 
        
        if role == "student":
            if random() < epsilon: ax, ay = student_ai._find_random_empty(board.grid)
            else: ax, ay = student_ai.get_move(board.grid, current_color)
            move_immediate_reward = calculate_move_quality(board.grid, ax, ay, current_color)
        else:
            make_mistake = (p1 == "student") and (random() < TEACHER_MISTAKE_RATE)
            if make_mistake: ax, ay = teacher_ai._find_random_empty(board.grid)
            else:
                ax, ay = teacher_ai.get_move(board.grid, last_xy[0], last_xy[1], current_color)
                if not board.is_empty(ax, ay): ax, ay = teacher_ai._find_random_empty(board.grid)
                 
        target_policy = np.zeros(225)
        target_policy[ax * 15 + ay] = 1.0
        
        game_history.append({
            'state': state_tensor, 'policy': target_policy,
            'color': current_color, 'immediate_reward': move_immediate_reward
        })
        
        board.place_stone(ax, ay, current_color)
        last_xy = (ax, ay)
        
        if board.check_win(ax, ay, current_color):
            winner_color = current_color
            game_over = True
        elif board.is_full():
            winner_color = 0
            game_over = True
            
        current_color *= -1
        
    student_played = (p1 == "student")
    return game_history, winner_color, student_played

def train():
    import tensorflow as tf
    
    # 1. Setup Paths
    latest_model_path = os.path.join(MODEL_SAVE_PATH, "connect6_rl_model_latest.keras")
    final_model_path = os.path.join(MODEL_SAVE_PATH, "connect6_rl_model_final.keras")
    
    model_to_load = None
    if os.path.exists(latest_model_path): model_to_load = latest_model_path
    elif os.path.exists(final_model_path): model_to_load = final_model_path
        
    if model_to_load:
        print(f"✅ Found Connect-6 Model: {model_to_load}")
        student_ai = RL_AIPlayer(model_path=model_to_load)
    else:
        print(f"🚀 Starting New Training for Connect-6!")
        student_ai = RL_AIPlayer()
    
    # 2. Setup Variables
    num_workers = mp.cpu_count()
    memory_buffer = []
    epsilon = EPSILON_START
    games_completed = 0
    batch_count = 0
    
    # [NEW] Win Rate Counters
    recent_student_wins = 0
    recent_teacher_wins = 0
    recent_draws = 0
    recent_games_count = 0
    
    # 3. Training Loop
    with mp.Pool(processes=num_workers) as pool:
        with tqdm(total=NUM_TOTAL_GAMES, unit="game") as pbar:
            while games_completed < NUM_TOTAL_GAMES:
                current_weights = student_ai.model.get_weights()
                tasks = [(current_weights, epsilon)] * GAMES_PER_BATCH
                results = pool.map(simulation_worker, tasks)
                
                batch_games_count = len(results)
                games_completed += batch_games_count
                pbar.update(batch_games_count)
                
                for history, winner, student_played in results:
                    # [NEW] Count wins/losses for the report
                    if student_played:
                        recent_games_count += 1
                        if winner == 1: recent_student_wins += 1
                        elif winner == -1: recent_teacher_wins += 1
                        else: recent_draws += 1

                    # Reward calculation
                    reward_for_black = 0
                    if winner == 1: reward_for_black = 1.0
                    elif winner == -1: reward_for_black = -1.0
                    else: reward_for_black = -0.1 
                    
                    for step in history:
                        base_val = reward_for_black if step['color'] == 1 else -reward_for_black
                        final_val = base_val + step['immediate_reward']
                        final_val = np.clip(final_val, -1.5, 1.5)
                        aug_data = get_symmetries(step['state'], step['policy'])
                        for s, p in aug_data: memory_buffer.append((s, p, final_val))

                # Train Model
                if len(memory_buffer) >= TRAIN_THRESHOLD:
                    states = np.vstack([m[0] for m in memory_buffer])
                    policies = np.vstack([m[1] for m in memory_buffer])
                    values = np.array([m[2] for m in memory_buffer])
                    student_ai.model.fit(states, {'policy_output': policies, 'value_output': values}, batch_size=512, epochs=1, verbose=0)
                    memory_buffer = []
                    if epsilon > EPSILON_END: epsilon *= EPSILON_DECAY
                
                # [NEW] Update Progress Bar with Win Rate
                if recent_games_count > 0:
                    win_rate = (recent_student_wins / recent_games_count) * 100
                    pbar.set_postfix({'WR': f"{win_rate:.1f}%", 'Eps': f"{epsilon:.2f}"})

                # [NEW] Print Detailed Report
                batch_count += 1
                if batch_count % REPORT_EVERY == 0:
                     if recent_games_count > 0:
                        wr = (recent_student_wins / recent_games_count) * 100
                        tqdm.write(f"\n[Battle Report] Games: {recent_games_count} | Student Wins: {recent_student_wins} | Teacher Wins: {recent_teacher_wins} (Win Rate: {wr:.1f}%)")
                        # Reset counters
                        recent_student_wins = 0
                        recent_teacher_wins = 0
                        recent_draws = 0
                        recent_games_count = 0

                if batch_count % SAVE_MODEL_EVERY == 0:
                    student_ai.save_model(latest_model_path)
    
    student_ai.save_model(final_model_path)
    print("Connect 6 Training Complete!")

if __name__ == "__main__":
    mp.set_start_method("spawn", force=True)
    train()