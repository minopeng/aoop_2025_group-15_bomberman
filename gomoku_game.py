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
        self.running = True
        self.game_over = False
        self.current_player_color = 1 
        self.dot_list = [(25 + i * 50 - self.img_white.get_width() / 2, 25 + j * 50 - self.img_white.get_height() / 2) 
                         for i in range(LEVEL) for j in range(LEVEL)]
        self.last_move_x = -1
        self.last_move_y = -1

    def run(self):
        self.game_mode = self.menu.run()
        if self.game_mode is None: self.running = False 
        self.screen.blit(self.img_bg, (0, 0))
        pygame.display.update()
        while self.running:
            self._handle_events()
            if self.game_over:
                print("Game Over. 5秒後關閉...")
                sleep(5)
                self.running = False
        pygame.quit()
        exit()

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: self.running = False
            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                self._handle_mouse_click(event.pos)

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
        self.board.place_stone(m, n, color)
        stone_img = self.img_black if color == 1 else self.img_white
        self.screen.blit(stone_img, self.dot_list[LEVEL * m + n])
        pygame.display.update()
        
        if self.board.check_win(m, n, color):
            self.game_over = True
            self._show_winner_message(color)
            return
        if self.board.is_full():
            self.game_over = True
            self._show_winner_message(0)
            return
        if self.game_mode == 'pvp':
            self.current_player_color *= -1

    def _trigger_ai_move(self):
        ai_color = -1 
        # [關鍵] 使用 RL AI 的介面
        x, y = self.ai.get_move(self.board.grid, ai_color)
        
        if not (self.board.is_valid(x, y) and self.board.is_empty(x, y)):
            print("AI 發生錯誤，隨機下...")
            x, y = self.ai._find_random_empty(self.board.grid)
        
        self._execute_move(x, y, ai_color)

    def _show_winner_message(self, color):
        if color == 1: msg, rgb = 'Black Wins!', (0, 0, 0)
        elif color == -1: msg, rgb = 'White (AI) Wins!', (217, 20, 30)
        else: msg, rgb = 'Draw!', (100, 100, 100)
        text = self.font_m.render(msg, True, rgb)
        self.screen.blit(text, (80, 650))
        pygame.display.update()