# gomoku_game.py
# 測試模式：載入訓練好的 RL 模型

import pygame
from pygame.locals import *
from time import sleep
import os

# 匯入模組
from constants import *
from game_board import GameBoard
# [重點] 這裡我們要匯入 RL_AIPlayer (學生)
from rl_ai_player import RL_AIPlayer   
from start_menu import StartMenu
from ai_player import AIPlayer

class GomokuGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption("五子棋 RL AI 驗收測試")
        
        self.font_m = pygame.font.SysFont("黑体", 40)
        self.font_l = pygame.font.SysFont("黑体", 60)
        self.font_s = pygame.font.SysFont("黑体", 30)
        
        try:
            self.img_bg = pygame.image.load('./Res/bg.png').convert()
            img_white = pygame.image.load('./Res/white.png').convert_alpha()
            img_black = pygame.image.load('./Res/black.png').convert_alpha()
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
        except pygame.error as e:
            print(f"錯誤: 找不到圖片資源 - {e}")
            exit()

        self.board = GameBoard()
        
        # ----------------------------------------------------
        # [關鍵設定] 指定你要測試的模型檔案
        # 剛跑完訓練通常是存成這個名字：
        MODEL_FILE_TO_TEST = "models/gomoku_rl_model_final.keras"
        
        print(f"--- 正在載入 AI 模型: {MODEL_FILE_TO_TEST} ---")
        
        if not os.path.exists(MODEL_FILE_TO_TEST):
            print(f"❌ 錯誤：找不到模型檔案！請確認 train.py 是否跑完並存檔。")
            print(f"搜尋路徑: {MODEL_FILE_TO_TEST}")
            exit()
            
        try:
            # 載入模型
            self.ai = RL_AIPlayer(model_path=MODEL_FILE_TO_TEST)
            print("✅ 模型載入成功！準備開戰！")
        except Exception as e:
            print(f"❌ 模型載入失敗: {e}")
            exit()
        # ----------------------------------------------------
        
        self.menu = StartMenu(self.screen, self.img_bg, self.font_l, self.font_s)
        self.game_mode = None 
        self.rule_length = 5
        self.running = True
        self.game_over = False
        self.current_player_color = 1 
        self.dot_list = [(25 + i * 50 - self.img_white.get_width() / 2, 25 + j * 50 - self.img_white.get_height() / 2) 
                         for i in range(LEVEL) for j in range(LEVEL)]
        self.last_move_x = -1
        self.last_move_y = -1
        self.hint_pos = None  # Stores (x, y) of the hint
        self.hint_ai = None   # We will create this when the game starts

    def run(self):
        running = True
        while running:
            # --- Step 1: Show Start Menu ---
            # [Updated] Now receives (mode, length)
            mode, length = self.menu.run()
            
            if mode is None:
                running = False
                break

            self.game_mode = mode
            self.rule_length = length
            self.hint_ai = AIPlayer(target_length=self.rule_length)
            print(f"Starting Game: {mode.upper()} | Rule: {length}-in-a-row")

            # --- Step 2: Start Match ---
            self._reset_game_state()
            self._play_match()
            
            # --- Step 3: End ---
            pygame.time.wait(2000) 

        pygame.quit()
        exit()

    def _reset_game_state(self):
        """Initialize board with the selected rule length"""
        # [Updated] Pass the selected rule length to Board
        self.board = GameBoard(target_length=self.rule_length)
        
        self.game_over = False
        self.winner = 0
        self.current_player_color = 1
        self.screen.blit(self.img_bg, (0, 0))
        pygame.display.update()

    def _play_match(self):
        """Blocks here running the game until self.game_over becomes True"""
        while not self.game_over:
            self._handle_events()
            # (The rest of your game logic happens inside _handle_events -> _execute_move)
            
            # CPU optimization
            if self.game_mode == 'ai' and self.current_player_color == -1:
                pass
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: 
                pygame.quit()
                exit()
            
            # [NEW] Handle Keyboard Input
            if event.type == KEYDOWN:
                if event.key == K_u and not self.game_over: # Press 'U' to Undo
                    self._undo_move()
                
                # [FIX] This must be INDENTED inside KEYDOWN
                if event.key == K_h and not self.game_over:
                    self._show_hint()

            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                if self.game_mode == 'ai' and self.current_player_color == -1:
                    continue 
                self._handle_mouse_click(event.pos)

    # [NEW] Add this logic function
    def _undo_move(self):
        """Handles the logic for undoing moves."""
        print("Undo requested...")
        
        if self.game_mode == 'pvp':
            # In PvP, undo 1 move and switch turn back
            if self.board.undo_last_move():
                self.current_player_color *= -1
                self._redraw_board()
                
        elif self.game_mode == 'ai':
            # In AI mode, we must undo TWO moves (AI's and Player's)
            # to let the player try again.
            if len(self.board.history) >= 2:
                self.board.undo_last_move() # Undo AI
                self.board.undo_last_move() # Undo Player
                self._redraw_board()
            elif len(self.board.history) == 1:
                # Rare case: Player moved, AI crashed/didn't move yet
                self.board.undo_last_move()
                self._redraw_board()

    # [NEW] Helper to refresh the screen after undoing
    def _redraw_board(self):
        self.screen.blit(self.img_bg, (0, 0))
        
        # 1. Draw all stones
        for x in range(LEVEL):
            for y in range(LEVEL):
                color = self.board.grid[x][y]
                if color != 0:
                    stone_img = self.img_black if color == 1 else self.img_white
                    self.screen.blit(stone_img, self.dot_list[LEVEL * x + y])
        
        # 2. [NEW] Draw Hint (if it exists)
        if self.hint_pos:
            hx, hy = self.hint_pos
            # Get the pixel coordinates from your dot_list
            # Note: dot_list stores (left, top) for images. Center is + width/2
            px, py = self.dot_list[LEVEL * hx + hy]
            
            # Adjust to center (since dot_list is top-left of the image)
            center_x = int(px + self.img_black.get_width() / 2)
            center_y = int(py + self.img_black.get_height() / 2)
            
            # Draw a transparent-ish red circle (or solid red ring)
            pygame.draw.circle(self.screen, (255, 0, 0), (center_x, center_y), 10, 3) # Red Ring

        pygame.display.update()

    def _handle_mouse_click(self, pos):
        x, y = pos
        if not (25 <= x <= 725 and 25 <= y <= 725): return
        m = int(round((x - 25) / 50))
        n = int(round((y - 25) / 50))
        if not self.board.is_valid(m, n): return
        if not self.board.is_empty(m, n): return

        # 玩家落子
        self._execute_move(m, n, self.current_player_color)
        
        if self.game_mode == 'pvp': return

        # AI 落子
        if not self.game_over and self.game_mode == 'ai':
            pygame.display.update() 
            sleep(0.1)
            self._trigger_ai_move()

    def _execute_move(self, m, n, color):
        # 1. Clear the hint (if it was visible)
        self.hint_pos = None
        
        # 2. Update the Logical Board
        self.board.place_stone(m, n, color)
        
        # 3. Redraw the Screen
        # We MUST redraw everything to remove the "Red Ring" hint if it was there.
        # This replaces the old single-stone blit.
        self._redraw_board()
        
        # 4. Check Victory Conditions
        # The board knows if it's 5-row or 6-row based on how you initialized it.
        if self.board.check_win(m, n, color):
            self.game_over = True
            self.winner = color
            self._show_winner_message(color)
            return

        if self.board.is_full():
            self.game_over = True
            self.winner = 0  # 0 means Draw
            self._show_winner_message(0)
            return

        # 5. Switch Turns (Only for PvP)
        # In AI mode, the AI triggers its own move separately after this returns.
        if self.game_mode == 'pvp':
            self.current_player_color *= -1

    def _trigger_ai_move(self):
        ai_color = -1 
        
        # NOTE regarding AI:
        # The RL Model (Student) is trained for 5-in-a-row. 
        # If user selects 6, the RL AI might play poorly.
        # The Heuristic AI (Teacher) logic handles 6-in-a-row correctly if we update it.
        
        # Ideally, you should pass self.rule_length to your AI here if it supports it.
        # For now, assuming RL_AIPlayer uses the model:
        x, y = self.ai.get_move(self.board.grid, ai_color)
        
        self._execute_move(x, y, ai_color)

    def _show_winner_message(self, color):
        if color == 1: msg, rgb = 'Black Wins!', (0, 0, 0)
        elif color == -1: msg, rgb = 'White (AI) Wins!', (217, 20, 30)
        else: msg, rgb = 'Draw!', (100, 100, 100)
        text = self.font_m.render(msg, True, rgb)
        self.screen.blit(text, (80, 650))
        pygame.display.update()

    # [NEW] Calculate and show the hint
    def _show_hint(self):
        print("Thinking of a hint...")
        
        # 1. Configure the AI to skip "random openings" and think hard immediately
        self.hint_ai.ai_move_count = 100 
        
        # 2. Ask Teacher for the best move for the CURRENT player
        # We pass the current board and the current player's color
        x, y = self.hint_ai.get_move(self.board.grid, -1, -1, self.current_player_color)
        
        # 3. Store and Draw
        self.hint_pos = (x, y)
        self._redraw_board()