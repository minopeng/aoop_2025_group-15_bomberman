# rl_ai_player.py
# 這是「學生 AI」, 包含神經網路 (大腦)
# [修正版] 加入了 _find_random_empty 函式

import numpy as np
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers, Model
from tensorflow.keras.optimizers import Adam
from random import randint # [新增] 需要用到隨機

from constants import LEVEL, GRADE, MAX_SCORE

class RL_AIPlayer:
    """
    強化學習 (RL) 玩家
    使用一個雙頭 (Policy/Value) 神經網路
    """
    def __init__(self, model_path=None):
        self.level = LEVEL
        
        if model_path:
            # 載入訓練好
            self.model = keras.models.load_model(model_path)
            # print(f"從 {model_path} 載入模型。") 
            # 註解掉 print 以免多核心訓練時洗版
        else:
            # 建立一個新模型
            self.model = self._build_model()
            # print("建立一個新的空白模型。")

    def _build_model(self):
        """
        建立神經網路 (AI 的大腦)
        """
        # --- 共享的網路主幹 (CNN) ---
        board_input = layers.Input(shape=(self.level, self.level, 3), name="board_input")
        
        x = layers.Conv2D(64, (3, 3), padding='same', activation='relu')(board_input)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(64, (3, 3), padding='same', activation='relu')(x)
        x = layers.BatchNormalization()(x)
        x = layers.Conv2D(64, (3, 3), padding='same', activation='relu')(x)
        shared_features = layers.BatchNormalization()(x)

        # --- 1. 策略頭 (Policy Head) ---
        policy_conv = layers.Conv2D(2, (1, 1), padding='same', activation='relu')(shared_features)
        policy_flat = layers.Flatten()(policy_conv)
        policy_dense = layers.Dense(self.level * self.level, activation='softmax', name='policy_output')(policy_flat)

        # --- 2. 價值頭 (Value Head) ---
        value_conv = layers.Conv2D(1, (1, 1), padding='same', activation='relu')(shared_features)
        value_flat = layers.Flatten()(value_conv)
        value_dense = layers.Dense(64, activation='relu')(value_flat)
        value_output = layers.Dense(1, activation='tanh', name='value_output')(value_dense)

        # --- 建立並編譯模型 ---
        model = Model(inputs=board_input, outputs=[policy_dense, value_output])
        
        model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss={
                'policy_output': 'categorical_crossentropy',
                'value_output': 'mean_squared_error'
            }
        )
        return model

    def _prepare_input(self, board_grid, player_color):
        """
        將 15x15 的 list (0, 1, -1) 轉換為 (1, 15, 15, 3) 的 numpy 陣列
        """
        state = np.zeros((self.level, self.level, 3), dtype=np.float32)
        state[:, :, 0] = (np.array(board_grid) == player_color)
        state[:, :, 1] = (np.array(board_grid) == -player_color)
        state[:, :, 2] = 1.0 
        return np.expand_dims(state, axis=0)

    def get_move(self, board_grid, player_color):
        """
        AI 決策：根據目前局勢，決定下一步
        """
        board_tensor = self._prepare_input(board_grid, player_color)
        policy_probs, value = self.model.predict(board_tensor, verbose=0)
        
        policy_probs = policy_probs.reshape((self.level, self.level))
        legal_moves_mask = (np.array(board_grid) == 0)
        masked_probs = policy_probs * legal_moves_mask
        
        if np.sum(masked_probs) > 0:
            masked_probs /= np.sum(masked_probs)
        else:
            masked_probs = legal_moves_mask / np.sum(legal_moves_mask)

        move_index = np.argmax(masked_probs)
        x = move_index // self.level
        y = move_index % self.level
        
        return x, y

    # [新增] 這裡補上了遺失的函式！
    def _find_random_empty(self, board_grid):
        """隨機找一個棋盤上的空點"""
        empty_spots = []
        for i in range(self.level):
            for j in range(self.level):
                if board_grid[i][j] == 0:
                    empty_spots.append((i,j))
        
        if not empty_spots:
            return -1, -1 # 棋盤滿了
        
        return empty_spots[randint(0, len(empty_spots) - 1)]

    def train_on_memory(self, memory_buffer):
        """從「記憶」中學習"""
        state_tensors = np.vstack([m[0] for m in memory_buffer])
        actions_taken = [m[1] for m in memory_buffer] 
        final_rewards = np.array([m[2] for m in memory_buffer])

        value_targets = final_rewards
        policy_targets = np.zeros((len(actions_taken), self.level * self.level))
        
        # 這裡要注意：如果 action 傳進來的是 (x, y) tuple 或是 policy array
        # 我們的 train.py 傳進來的是 policy array，所以直接用
        # 但為了相容舊版邏輯，我們檢查一下
        
        # 在新的 train.py 中，m[1] 已經是 policy array 了，所以不需要轉換
        policy_targets = np.vstack([m[1] for m in memory_buffer])

        self.model.fit(
            state_tensors,
            {
                'policy_output': policy_targets, 
                'value_output': value_targets
            },
            epochs=1,
            batch_size=64,
            verbose=0
        )

    def save_model(self, file_path="gomoku_rl_model.keras"):
        """儲存模型"""
        self.model.save(file_path)
        print(f"模型已儲存至 {file_path}")