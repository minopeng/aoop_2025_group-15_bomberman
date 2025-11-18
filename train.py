# train.py
# 這是 AI 的訓練場
# 它會讓「學生 AI」(RL) 和「老師 AI」(Heuristic) 對戰，並從中學習

import os
from tqdm import tqdm # 顯示進度條

# 匯入我們的遊戲模組
from game_board import GameBoard
from ai_player import AIPlayer         # 老師 (Heuristic AI)
from rl_ai_player import RL_AIPlayer   # 學生 (RL AI)

# --- 訓練超參數 ---
NUM_TRAINING_GAMES = 10000       # 總共要訓練的局數 (一萬局)
TRAIN_BUFFER_SIZE = 100        # 每 100 局, 拿記憶去訓練一次
SAVE_MODEL_EVERY = 1000          # 每 1000 局, 儲存一次模型
MODEL_SAVE_PATH = "models/"      # 模型儲存的資料夾

# 確保 models 資料夾存在
os.makedirs(MODEL_SAVE_PATH, exist_ok=True)


def train():
    """主訓練函式"""
    
    # 1. 建立「老師」和「學生」
    teacher_ai = AIPlayer()
    
    # 建立一個全新的、空白的「學生」模型
    student_ai = RL_AIPlayer() 
    
    # 2. 建立記憶體
    # 格式: [(state_tensor, action_tuple, reward), ...]
    memory_buffer = []
    
    # 3. 追蹤統計
    student_wins = 0
    teacher_wins = 0
    draws = 0

    print(f"--- 開始訓練 {NUM_TRAINING_GAMES} 局 ---")
    print(f"學生 (RL AI) vs. 老師 (Heuristic AI)")
    print(f"模型將儲存於: {MODEL_SAVE_PATH}")

    # 4. 主訓練迴圈
    for game_count in tqdm(range(1, NUM_TRAINING_GAMES + 1)):
        
        # --- 每局開始時, 重設一切 ---
        board = GameBoard()
        game_history = [] # 暫存這一局「學生」的 (狀態, 動作)
        
        # 為了簡化, 我們固定讓學生 (RL AI) 執黑棋 (1, 先手)
        # 老師 (Heuristic AI) 執白棋 (-1, 後手)
        student_color = 1
        teacher_color = -1
        
        game_over = False
        reward = 0
        student_last_move_xy = (-1, -1) # 老師 AI 需要這個
        
        
        # --- 5. 單局遊戲迴圈 ---
        while not game_over:
            
            # --- A. 學生 (RL AI) 的回合 ---
            
            # 取得當前狀態, 準備送入神經網路
            current_state_tensor = student_ai._prepare_input(board.grid, student_color)
            
            # 學生 AI 決定下一步
            x, y = student_ai.get_move(board.grid, student_color)
            
            # 儲存「學生的決策」: (在 *這個狀態* 下, 走了 *(x, y)* 這一步)
            game_history.append((current_state_tensor, (x, y)))
            
            # 落子
            board.place_stone(x, y, student_color)
            student_last_move_xy = (x, y) # 記錄這一步, 給老師看
            
            # 檢查學生是否勝利
            if board.check_win(x, y, student_color):
                game_over = True
                reward = 1 # 學生贏了, 獎勵 +1
                student_wins += 1
                break
                
            # 檢查平局
            if board.is_full():
                game_over = True
                reward = 0 # 平局, 獎勵 0
                draws += 1
                break

            # --- B. 老師 (Heuristic AI) 的回合 ---
            
            # 老師 AI 決定下一步 (它需要知道學生上一步下在哪)
            tx, ty = teacher_ai.get_move(board.grid, student_last_move_xy[0], student_last_move_xy[1], teacher_color)
            
            # [重要] 驗證老師的棋步, 防止它出錯 (例如選到已佔用的)
            if not board.is_empty(tx, ty):
                print(f"警告: 老師 AI 算錯, 隨機找空位...")
                tx, ty = teacher_ai._find_random_empty(board.grid)
            
            # 萬一連隨機都找不到 (平局), 提早結束
            if (tx, ty) == (-1, -1):
                game_over = True
                reward = 0
                draws += 1
                break
                
            # 落子
            board.place_stone(tx, ty, teacher_color)
            
            # 檢查老師是否勝利
            if board.check_win(tx, ty, teacher_color):
                game_over = True
                reward = -1 # 學生輸了, 獎勵 -1
                teacher_wins += 1
                break

            # (平局檢查在學生回合做過即可)

        # --- 6. 遊戲結束, 整理記憶 ---
        # 這一局的「最終結果 (reward)」, 要套用到學生這一局的「每一步」
        for state, action in game_history:
            memory_buffer.append((state, action, reward))
            
        # --- 7. 檢查是否該訓練了 ---
        if game_count % TRAIN_BUFFER_SIZE == 0 and memory_buffer:
            print(f"\n[訓練] 遊戲局數 {game_count}, 達到 {len(memory_buffer)} 筆記憶, 開始訓練...")
            
            # 呼叫學生 AI 進行學習
            student_ai.train_on_memory(memory_buffer)
            memory_buffer = [] # 訓練完清空記憶

            # 顯示最近 {TRAIN_BUFFER_SIZE} 局的戰況
            print(f"[統計] 學生 wins: {student_wins}, 老師 wins: {teacher_wins}, Draws: {draws}")
            student_wins, teacher_wins, draws = 0, 0, 0 # 重設計數器
            
        # --- 8. 檢查是否該儲存模型了 ---
        if game_count % SAVE_MODEL_EVERY == 0:
            save_filename = os.path.join(MODEL_SAVE_PATH, f"gomoku_rl_model_game_{game_count}.keras")
            student_ai.save_model(save_filename)


    # --- 訓練迴圈結束 ---
    print("--- 訓練完成 ---")
    
    # 儲存最終的模型
    final_model_path = os.path.join(MODEL_SAVE_PATH, "gomoku_rl_model_final.keras")
    student_ai.save_model(final_model_path)
    print(f"最終模型已儲存至: {final_model_path}")


# 程式進入點
if __name__ == "__main__":
    train()