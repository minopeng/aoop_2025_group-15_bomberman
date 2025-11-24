# gomoku_game.py
# 包含 GomokuGame 類別 (主控制器)

import pygame
from pygame.locals import *
from time import sleep

# 匯入我們的自訂模組
from constants import *
from game_board import GameBoard
from ai_player import AIPlayer
from start_menu import StartMenu

class GomokuGame:
    """遊戲總指揮，管理主迴圈、事件和繪圖"""
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption("五子棋 OOP 對戰 (多檔案)")
        
        # 載入資源 (字體)
        self.font_m = pygame.font.SysFont("黑体", 40)
        self.font_l = pygame.font.SysFont("黑体", 60)
        self.font_s = pygame.font.SysFont("黑体", 30)
        
        # 載入資源 (圖片)
        try:
            self.img_bg = pygame.image.load('./Res/bg.png').convert()
            img_white = pygame.image.load('./Res/white.png').convert_alpha()
            img_black = pygame.image.load('./Res/black.png').convert_alpha()
            
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
        except pygame.error as e:
            print(f"錯誤: 找不到圖片資源 (請確認 './Res/' 資料夾和圖片都在) - {e}")
            exit()

        # 遊戲物件
        self.board = GameBoard() # 從 game_board.py 建立
        self.ai = AIPlayer()     # 從 ai_player.py 建立
        self.menu = StartMenu(self.screen, self.img_bg, self.font_l, self.font_s) # 從 start_menu.py 建立

        # 遊戲狀態
        self.game_mode = None 
        self.running = True
        self.game_over = False
        self.current_player_color = 1 # 永遠黑棋 (1) 先手
        
        self.dot_list = [(25 + i * 50 - self.img_white.get_width() / 2, 25 + j * 50 - self.img_white.get_height() / 2) 
                         for i in range(LEVEL) for j in range(LEVEL)]
                         
        self.last_move_x = -1
        self.last_move_y = -1

    def run(self):
        """遊戲主進入點"""
        self.game_mode = self.menu.run()
        if self.game_mode is None:
            self.running = False 
        
        self.screen.blit(self.img_bg, (0, 0))
        pygame.display.update()
        
        while self.running:
            self._handle_events()
            
            if self.game_over:
                print("Game Over. Closing in 5 seconds.")
                sleep(5)
                self.running = False

        pygame.quit()
        exit()

    def _handle_events(self):
        """處理所有事件 (退出、滑鼠點擊)"""
        for event in pygame.event.get():
            if event.type == QUIT:
                self.running = False
            
            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                self._handle_mouse_click(event.pos)

    def _handle_mouse_click(self, pos):
        """處理滑鼠點擊邏輯"""
        x, y = pos
        
        if not (25 <= x <= 725 and 25 <= y <= 725):
            return

        m = int(round((x - 25) / 50))
        n = int(round((y - 25) / 50))
        
        if not self.board.is_valid(m, n):
            return

        if not self.board.is_empty(m, n):
            print("Overwrite~~")
            return

        # --- 落子成功 ---
        self._execute_move(m, n, self.current_player_color)
        
        self.last_move_x = m
        self.last_move_y = n
        
        if not self.game_over and self.game_mode == 'ai':
            pygame.display.update() 
            sleep(0.1)
            self._trigger_ai_move()

    def _execute_move(self, m, n, color):
        """執行一步棋 (落子、繪圖、檢查勝利、換邊)"""
        
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

        self.current_player_color *= -1

    def _trigger_ai_move(self):
        """觸發 AI 進行下一步"""
        ai_color = -1
        
        x, y = self.ai.get_move(self.board.grid, self.last_move_x, self.last_move_y, ai_color)
        
        if not (self.board.is_valid(x, y) and self.board.is_empty(x, y)):
            print("AI Error! Finding random spot...")
            x, y = self.ai._find_random_empty(self.board.grid)
            if (x, y) == (-1, -1):
                self.game_over = True
                self._show_winner_message(0)
                return
        
        self._execute_move(x, y, ai_color)

    def _show_winner_message(self, color):
        """在畫面上顯示勝利訊息"""
        if color == 1:
            msg = 'GAME OVER, Black is win!'
            color_rgb = (110, 210, 30)
        elif color == -1:
            msg = 'GAME OVER, White is win!'
            color_rgb = (217, 20, 30)
        else:
            msg = 'GAME OVER, Draw!'
            color_rgb = (100, 100, 100)
            
        text = self.font_m.render(msg, True, color_rgb)
        self.screen.blit(text, (80, 650))
        pygame.display.update()