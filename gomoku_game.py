# gomoku_game.py
# 包含 Ghost Stone (落子預覽) 功能的完整版本

import pygame
from pygame.locals import *
from time import sleep
import os
import sys

# --- Custom Module Imports ---
from constants import *
from game_board import GameBoard
from rl_ai_player import RL_AIPlayer   
from start_menu import StartMenu
from ai_player import AIPlayer
from go_engine import GoEngine  

class GomokuGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption("Board Game AI Arena")
        
        self.font_m = pygame.font.SysFont("黑体", 40)
        self.font_l = pygame.font.SysFont("黑体", 60)
        self.font_s = pygame.font.SysFont("黑体", 30)
        
        try:
            self.img_bg = pygame.image.load('./Res/bg.png').convert()
            img_white = pygame.image.load('./Res/white.png').convert_alpha()
            img_black = pygame.image.load('./Res/black.png').convert_alpha()
            
            # 調整棋子大小
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
            
            # [新增] 預先製作「半透明 (Ghost)」版本的棋子
            # copy() 複製一份，set_alpha(128) 設定為半透明 (0=全透, 255=不透)
            self.img_white_ghost = self.img_white.copy()
            self.img_white_ghost.set_alpha(128)
            self.img_black_ghost = self.img_black.copy()
            self.img_black_ghost.set_alpha(128)
            
        except pygame.error as e:
            print(f"❌ Error: Missing resources - {e}")
            sys.exit()

        self.board = GameBoard()
        self.menu = StartMenu(self.screen, self.img_bg, self.font_l, self.font_s)
        self.ai = None
        self.hint_ai = None
        self.go_engine = None 
        
        self.game_mode = None 
        self.rule_length = 5
        self.running = True
        self.game_over = False
        self.force_quit_to_menu = False 
        self.winner = 0
        self.current_player_color = 1 
        
        # Go-specific variables
        self.pass_count = 0
        self.final_score_text = "" 
        
        self.dot_list = [(25 + i * 50 - self.img_white.get_width() / 2, 25 + j * 50 - self.img_white.get_height() / 2) 
                         for i in range(LEVEL) for j in range(LEVEL)]
        
        self.hint_pos = None
        
        # [新增] 紀錄目前 Ghost Stone 的位置 (grid_x, grid_y)
        self.ghost_pos = None

    def run(self):
        while self.running:
            mode, length = self.menu.run()
            
            if mode is None:
                self.running = False
                break

            self.game_mode = mode
            self.rule_length = length
            
            if mode == 'ai':
                if length == 'go':
                    print("AI not supported for Go. Switching to PvP.")
                    self.game_mode = 'pvp'
                else:
                    self._load_ai_model(length)
            
            # Load Hint AI (Heuristic)
            if length != 'go':
                self.hint_ai = AIPlayer(target_length=self.rule_length)
            
            label = "Go (Weiqi)" if length == 'go' else f"Rule: {length}"
            print(f"\n--- 🎮 Starting Game: {mode.upper()} | {label} ---")

            self._reset_game_state()
            self._play_match()
            
            if self.force_quit_to_menu:
                print("↩️  Returned to Menu")
                continue

            if self.running: 
                self._wait_for_menu_input()

        pygame.quit()
        sys.exit()

    def _wait_for_menu_input(self):
        # Fancy Game Over Screen
        print("Game Over. Waiting for 'R'...")
        
        if self.rule_length == 'go':
            win_text = self.final_score_text
            win_color = (255, 215, 0)
        else:
            if self.winner == 1: win_text, win_color = "Black Wins!", (50, 255, 50)
            elif self.winner == -1: win_text, win_color = "White Wins!", (255, 80, 80)
            else: win_text, win_color = "Draw Game!", (200, 200, 200)

        prompt_text = "Press 'R' to Return to Menu"
        
        alpha = 0  
        scale = 1.0
        scale_dir = 0.01 
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 20, 20)) 
        
        clock = pygame.time.Clock()
        waiting = True
        
        while waiting:
            clock.tick(60) 
            
            for event in pygame.event.get():
                if event.type == QUIT: self.running = False; waiting = False; return
                if event.type == KEYDOWN and event.key == K_r: waiting = False; return

            if alpha < 210: alpha += 2 
            overlay.set_alpha(alpha)
            
            scale += scale_dir
            if scale > 1.05 or scale < 0.95: scale_dir *= -1
                
            self.screen.blit(overlay, (0, 0))
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            
            surf_win = self.font_l.render(win_text, True, win_color)
            w = int(surf_win.get_width() * scale)
            h = int(surf_win.get_height() * scale)
            scaled_win = pygame.transform.smoothscale(surf_win, (w, h))
            win_rect = scaled_win.get_rect(center=(center_x, center_y - 30))
            
            shadow = self.font_l.render(win_text, True, (0, 0, 0))
            scaled_shadow = pygame.transform.smoothscale(shadow, (w, h))
            shadow_rect = scaled_shadow.get_rect(center=(center_x + 3, center_y - 27))
            self.screen.blit(scaled_shadow, shadow_rect)
            self.screen.blit(scaled_win, win_rect)
            
            if pygame.time.get_ticks() % 1500 < 800: 
                surf_prompt = self.font_s.render(prompt_text, True, (200, 200, 200))
                prompt_rect = surf_prompt.get_rect(center=(center_x, center_y + 60))
                self.screen.blit(surf_prompt, prompt_rect)
                
            pygame.display.update()

    def _load_ai_model(self, length):
        if length == 'go': return 
        model_path = ""
        if length == 4: model_path = "models/connect4_graduation.keras"
        elif length == 5: model_path = "models/gomoku_rl_model_final.keras"
        elif length == 6: model_path = "models/connect6_rl_model_latest.keras"

        print(f"🧠 Loading AI for Rule {length}: {model_path}")
        if os.path.exists(model_path):
            try:
                self.ai = RL_AIPlayer(model_path=model_path)
                print("✅ AI Loaded Successfully!")
            except Exception as e:
                print(f"❌ Error: {e}")
                self.ai = RL_AIPlayer()
        else:
            print(f"⚠️ Not found: {model_path}")
            self.ai = RL_AIPlayer() 

    def _reset_game_state(self):
        t_len = 5 if self.rule_length == 'go' else self.rule_length
        self.board = GameBoard(target_length=t_len)
        
        if self.rule_length == 'go':
            self.go_engine = GoEngine(self.board.grid)
            self.pass_count = 0
            self.final_score_text = ""
            
        self.game_over = False
        self.force_quit_to_menu = False 
        self.winner = 0
        self.current_player_color = 1 
        self.hint_pos = None
        self.ghost_pos = None # Reset ghost
        
        self.screen.blit(self.img_bg, (0, 0))
        pygame.display.update()

    def _play_match(self):
        while not self.game_over:
            self._handle_events()
            if self.game_mode == 'ai' and self.current_player_color == -1:
                pass
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: 
                pygame.quit(); sys.exit()
            
            if event.type == KEYDOWN:
                if event.key == K_r: self.force_quit_to_menu = True; self.game_over = True; return
                if event.key == K_p and self.rule_length == 'go' and not self.game_over: self._handle_go_pass()
                if event.key == K_u and not self.game_over: self._undo_move()
                if event.key == K_h and not self.game_over: self._show_hint()

            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                if self.game_mode == 'ai' and self.current_player_color == -1: continue 
                self._handle_mouse_click(event.pos)

            # [新增] 處理滑鼠移動 -> 更新 Ghost Stone
            if event.type == MOUSEMOTION and not self.game_over:
                # 如果是 AI 思考時間，不顯示 Ghost
                if self.game_mode == 'ai' and self.current_player_color == -1:
                    if self.ghost_pos is not None:
                        self.ghost_pos = None
                        self._redraw_board()
                    continue
                
                self._update_ghost_pos(event.pos)

    # [新增] 更新 Ghost 位置邏輯
    def _update_ghost_pos(self, pos):
        x, y = pos
        # 1. 檢查是否在棋盤範圍內
        if not (25 <= x <= 725 and 25 <= y <= 725):
            if self.ghost_pos is not None:
                self.ghost_pos = None
                self._redraw_board()
            return

        # 2. 轉換座標
        m = int(round((x - 25) / 50))
        n = int(round((y - 25) / 50))

        # 3. 檢查是否合法 (位置是否為空)
        # 注意：Go 模式要檢查 go_engine，其他模式檢查 board
        is_valid_spot = False
        if self.rule_length == 'go':
            # 簡單檢查 grid 是否為空即可，自殺規則太複雜不需要在 ghost 階段檢查
            if 0 <= m < LEVEL and 0 <= n < LEVEL and self.board.grid[m][n] == 0:
                is_valid_spot = True
        else:
            if self.board.is_valid(m, n) and self.board.is_empty(m, n):
                is_valid_spot = True

        # 4. 更新狀態
        new_ghost = (m, n) if is_valid_spot else None
        
        # 只有當位置改變時才重繪 (優化效能)
        if new_ghost != self.ghost_pos:
            self.ghost_pos = new_ghost
            self._redraw_board()

    def _handle_go_pass(self):
        print(f"Player {self.current_player_color} Passed!")
        self.pass_count += 1
        self.current_player_color *= -1
        if self.pass_count >= 2: self._end_go_game()

    def _end_go_game(self):
        print("Both passed. Calculating score...")
        black_score, white_score = self.go_engine.calculate_score()
        print(f"Black: {black_score}, White: {white_score}")
        
        if black_score > white_score:
            self.winner = 1
            self.final_score_text = f"Black Wins! (B:{black_score} vs W:{white_score})"
        elif white_score > black_score:
            self.winner = -1
            self.final_score_text = f"White Wins! (W:{white_score} vs B:{black_score})"
        else:
            self.winner = 0
            self.final_score_text = f"Draw! (Score: {black_score})"
        self.game_over = True

    def _undo_move(self):
        print("Undo requested...")
        if self.rule_length == 'go':
            if self.go_engine.undo():
                self.current_player_color *= -1
                self._redraw_board()
            return
            
        if self.game_mode == 'pvp':
            if self.board.undo_last_move():
                self.current_player_color *= -1
                self._redraw_board()
        elif self.game_mode == 'ai':
            if len(self.board.history) >= 2:
                self.board.undo_last_move(); self.board.undo_last_move()
                self._redraw_board()
            elif len(self.board.history) == 1:
                self.board.undo_last_move(); self._redraw_board()

    def _redraw_board(self):
        self.screen.blit(self.img_bg, (0, 0))
        
        # 1. 畫現有棋子
        for x in range(LEVEL):
            for y in range(LEVEL):
                color = self.board.grid[x][y]
                if color != 0:
                    stone_img = self.img_black if color == 1 else self.img_white
                    self.screen.blit(stone_img, self.dot_list[LEVEL * x + y])
        
        # 2. [新增] 畫 Ghost Stone (預覽)
        if self.ghost_pos:
            gx, gy = self.ghost_pos
            # 根據當前玩家顏色決定顯示黑或白
            ghost_img = self.img_black_ghost if self.current_player_color == 1 else self.img_white_ghost
            self.screen.blit(ghost_img, self.dot_list[LEVEL * gx + gy])

        # 3. 畫最後一手標記 (紅點)
        if self.rule_length != 'go' and self.board.history:
            last_x, last_y = self.board.history[-1]
            px, py = self.dot_list[LEVEL * last_x + last_y]
            center_x = int(px + self.img_black.get_width() / 2)
            center_y = int(py + self.img_black.get_height() / 2)
            pygame.draw.circle(self.screen, (220, 50, 50), (center_x, center_y), 5)

        # 4. 畫提示 (紅圈)
        if self.hint_pos:
            hx, hy = self.hint_pos
            px, py = self.dot_list[LEVEL * hx + hy]
            center_x = int(px + self.img_black.get_width() / 2)
            center_y = int(py + self.img_black.get_height() / 2)
            pygame.draw.circle(self.screen, (255, 0, 0), (center_x, center_y), 10, 3) 
            
        pygame.display.update()

    def _handle_mouse_click(self, pos):
        x, y = pos
        if not (25 <= x <= 725 and 25 <= y <= 725): return
        m = int(round((x - 25) / 50))
        n = int(round((y - 25) / 50))
        
        if self.rule_length == 'go':
            self._execute_go_move(m, n, self.current_player_color)
        else:
            if not self.board.is_valid(m, n): return
            if not self.board.is_empty(m, n): return
            self._execute_move(m, n, self.current_player_color)
            if self.game_mode == 'ai' and not self.game_over:
                pygame.display.update(); sleep(0.1); self._trigger_ai_move()

    def _execute_go_move(self, m, n, color):
        self.pass_count = 0
        success, captures = self.go_engine.place_stone(m, n, color)
        if not success: return 
        if captures: print(f"Captured {len(captures)} stones!")
        
        # Sync grid data to board object (important for saving/loading if needed)
        self.board.grid = self.go_engine.grid
        
        self._redraw_board()
        self.current_player_color *= -1

    def _execute_move(self, m, n, color):
        self.hint_pos = None 
        self.ghost_pos = None # Clear ghost immediately after click
        
        self.board.place_stone(m, n, color)
        self._redraw_board()
        
        if self.board.check_win(m, n, color):
            self.game_over = True; self.winner = color; self._show_winner_message(color); return
        if self.board.is_full():
            self.game_over = True; self.winner = 0; self._show_winner_message(0); return
        if self.game_mode == 'pvp':
            self.current_player_color *= -1

    def _trigger_ai_move(self):
        if self.rule_length == 'go': return
        ai_color = -1 
        x, y = self.ai.get_move(self.board.grid, ai_color)
        self._execute_move(x, y, ai_color)

    def _show_winner_message(self, color):
        # This function is mostly superseded by _wait_for_menu_input's fancy screen
        # but we keep it to show the result immediately before the loop ends.
        pass # logic moved to _wait_for_menu_input for better animation control

    def _show_hint(self):
        if self.rule_length == 'go': return
        self.hint_ai.ai_move_count = 100 
        x, y = self.hint_ai.get_move(self.board.grid, -1, -1, self.current_player_color)
        self.hint_pos = (x, y)
        self._redraw_board()

if __name__ == "__main__":
    game = GomokuGame()
    game.run()