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
        pygame.mixer.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption("Board Game AI Arena")
        
        self.font_m = pygame.font.SysFont("黑体", 40)
        self.font_l = pygame.font.SysFont("黑体", 60)
        self.font_s = pygame.font.SysFont("黑体", 30)
        
        try:
            # --- Load Images (For Classic Theme) ---
            self.img_bg = pygame.image.load('./Res/bg.png').convert()
            img_white = pygame.image.load('./Res/white.png').convert_alpha()
            img_black = pygame.image.load('./Res/black.png').convert_alpha()
            
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
            
            # [Ghost] Semi-transparent stones for Classic
            self.img_white_ghost = self.img_white.copy()
            self.img_white_ghost.set_alpha(128)
            self.img_black_ghost = self.img_black.copy()
            self.img_black_ghost.set_alpha(128)

            # [Sound]
            self.sound_move = pygame.mixer.Sound('./Res/drop.wav')
            self.sound_move.set_volume(0.8)
            self.sound_win = pygame.mixer.Sound('./Res/win.wav')
            self.sound_win.set_volume(1.0)
            self.sound_loss = pygame.mixer.Sound('./Res/loss.wav')
            self.sound_loss.set_volume(1.0)
            
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
        self.current_theme = 'Classic' # [新增] 目前主題
        
        self.running = True
        self.game_over = False
        self.force_quit_to_menu = False 
        self.winner = 0
        self.current_player_color = 1 
        self.pass_count = 0
        self.final_score_text = "" 
        
        self.dot_list = [(25 + i * 50, 25 + j * 50) for i in range(LEVEL) for j in range(LEVEL)]
        
        self.hint_pos = None
        self.ghost_pos = None 

    def run(self):
        while self.running:
            # 接收選單回傳的 (mode, length, theme)
            mode, length, theme = self.menu.run()
            
            if mode is None:
                self.running = False
                break

            self.game_mode = mode
            self.rule_length = length
            self.current_theme = theme # [更新主題]
            
            if mode == 'ai':
                if length == 'go':
                    print("AI not supported for Go. Switching to PvP.")
                    self.game_mode = 'pvp'
                else:
                    self._load_ai_model(length)
            
            if length != 'go':
                self.hint_ai = AIPlayer(target_length=self.rule_length)
            
            label = "Go (Weiqi)" if length == 'go' else f"Rule: {length}"
            print(f"\n--- 🎮 Starting Game: {mode.upper()} | {label} | Theme: {theme} ---")

            self._reset_game_state()
            self._play_match()
            
            if self.force_quit_to_menu:
                print("↩️  Returned to Menu")
                continue

            if self.running: 
                self._wait_for_menu_input()

        pygame.quit()
        sys.exit()

    def _prepare_replay_data(self):
        if self.rule_length == 'go': return [] 
        replay_data = []
        for (x, y) in self.board.history:
            color = self.board.grid[x][y]
            replay_data.append((x, y, color))
        return replay_data

    def _wait_for_menu_input(self):
        print("Game Over.")
        full_replay_history = self._prepare_replay_data()
        current_step = len(full_replay_history)
        max_step = len(full_replay_history)
        is_replaying = False 
        
        if self.rule_length == 'go':
            win_text = self.final_score_text
            win_color = (255, 215, 0) 
        else:
            if self.winner == 1: win_text, win_color = "Black Wins!", (50, 255, 50)
            elif self.winner == -1: win_text, win_color = "White Wins!", (255, 80, 80)
            else: win_text, win_color = "Draw Game!", (200, 200, 200)

        prompt_text = "Press 'R' to Return to Menu"
        replay_hint_text = "Replay: [<-] Back | [->] Fwd"
        
        alpha = 0  
        scale = 1.0
        scale_dir = 0.01 
        
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        overlay.fill((20, 20, 20)) 
        
        clock = pygame.time.Clock()
        waiting = True
        self.ghost_pos = None
        
        while waiting:
            clock.tick(60) 
            self._redraw_board(update=False)

            for event in pygame.event.get():
                if event.type == QUIT: self.running = False; waiting = False; return
                if event.type == KEYDOWN:
                    if event.key == K_r: waiting = False; return
                    if event.key == K_LEFT:
                        if self.rule_length == 'go':
                            if self.go_engine.undo(): is_replaying = True
                        else:
                            if current_step > 0:
                                self.board.undo_last_move(); current_step -= 1; is_replaying = True
                    if event.key == K_RIGHT:
                        if self.rule_length != 'go' and current_step < max_step:
                            nx, ny, nc = full_replay_history[current_step]
                            self.board.place_stone(nx, ny, nc)
                            current_step += 1; is_replaying = True; self.sound_move.play()

            target_alpha = 100 if is_replaying else 180 
            if alpha < target_alpha: alpha += 2 
            elif alpha > target_alpha: alpha -= 5
            overlay.set_alpha(alpha)
            
            scale += scale_dir
            if scale > 1.05 or scale < 0.95: scale_dir *= -1
                
            self.screen.blit(overlay, (0, 0))
            center_x, center_y = SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2
            
            if is_replaying:
                step_info = f"Step: {current_step} / {max_step}"
                surf_step = self.font_m.render(step_info, True, (100, 200, 255))
                self.screen.blit(surf_step, surf_step.get_rect(center=(center_x, 50)))
                surf_hint = self.font_s.render(replay_hint_text, True, (200, 200, 200))
                self.screen.blit(surf_hint, surf_hint.get_rect(center=(center_x, SCREEN_HEIGHT - 80)))
                surf_ret = self.font_s.render(prompt_text, True, (150, 150, 150))
                self.screen.blit(surf_ret, surf_ret.get_rect(center=(center_x, SCREEN_HEIGHT - 40)))
            else:
                surf_win = self.font_l.render(win_text, True, win_color)
                w, h = int(surf_win.get_width() * scale), int(surf_win.get_height() * scale)
                scaled_win = pygame.transform.smoothscale(surf_win, (w, h))
                win_rect = scaled_win.get_rect(center=(center_x, center_y - 30))
                
                shadow = self.font_l.render(win_text, True, (0, 0, 0))
                scaled_shadow = pygame.transform.smoothscale(shadow, (w, h))
                self.screen.blit(scaled_shadow, scaled_shadow.get_rect(center=(center_x + 3, center_y - 27)))
                self.screen.blit(scaled_win, win_rect)
                
                if pygame.time.get_ticks() % 2000 < 1000:
                    surf_rep = self.font_s.render(replay_hint_text, True, (150, 150, 150))
                    self.screen.blit(surf_rep, surf_rep.get_rect(center=(center_x, center_y + 40)))
                if pygame.time.get_ticks() % 1500 < 800: 
                    surf_pmt = self.font_s.render(prompt_text, True, (200, 200, 200))
                    self.screen.blit(surf_pmt, surf_pmt.get_rect(center=(center_x, center_y + 80)))
            
            pygame.display.update()

    def _load_ai_model(self, length):
        if length == 'go': return 
        model_path = ""
        if length == 4: model_path = "models/connect4_graduation.keras"
        elif length == 5: model_path = "models/gomoku_rl_model_final.keras"
        elif length == 6: model_path = "models/connect6_rl_model_latest.keras"

        if os.path.exists(model_path):
            try:
                self.ai = RL_AIPlayer(model_path=model_path)
            except: self.ai = RL_AIPlayer()
        else:
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
        self.ghost_pos = None 
        self._redraw_board() # First draw

    def _play_match(self):
        while not self.game_over:
            self._handle_events()
            if self.game_mode == 'ai' and self.current_player_color == -1: pass
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_r: self.force_quit_to_menu = True; self.game_over = True; return
                if event.key == K_p and self.rule_length == 'go' and not self.game_over: self._handle_go_pass()
                if event.key == K_u and not self.game_over: self._undo_move()
                if event.key == K_h and not self.game_over: self._show_hint()

            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                if self.game_mode == 'ai' and self.current_player_color == -1: continue 
                self._handle_mouse_click(event.pos)

            if event.type == MOUSEMOTION and not self.game_over:
                if self.game_mode == 'ai' and self.current_player_color == -1:
                    if self.ghost_pos: self.ghost_pos = None; self._redraw_board()
                    continue
                self._update_ghost_pos(event.pos)

    def _update_ghost_pos(self, pos):
        x, y = pos
        if not (25 <= x <= 725 and 25 <= y <= 725):
            if self.ghost_pos: self.ghost_pos = None; self._redraw_board()
            return
        m = int(round((x - 25) / 50))
        n = int(round((y - 25) / 50))
        is_valid = False
        if self.rule_length == 'go':
            if 0 <= m < LEVEL and 0 <= n < LEVEL and self.board.grid[m][n] == 0: is_valid = True
        else:
            if self.board.is_valid(m, n) and self.board.is_empty(m, n): is_valid = True
        new_ghost = (m, n) if is_valid else None
        if new_ghost != self.ghost_pos:
            self.ghost_pos = new_ghost
            self._redraw_board()

    def _handle_go_pass(self):
        self.pass_count += 1
        self.current_player_color *= -1
        if self.pass_count >= 2: self._end_go_game()

    def _end_go_game(self):
        b_s, w_s = self.go_engine.calculate_score()
        if b_s > w_s: self.winner = 1; self.final_score_text = f"Black Wins! ({b_s} vs {w_s})"; self.sound_win.play()
        elif w_s > b_s: self.winner = -1; self.final_score_text = f"White Wins! ({w_s} vs {b_s})"; self.sound_win.play()
        else: self.winner = 0; self.final_score_text = f"Draw! ({b_s})"; self.sound_loss.play()
        self.game_over = True

    def _undo_move(self):
        if self.rule_length == 'go':
            if self.go_engine.undo(): self.current_player_color *= -1; self._redraw_board()
            return
        if self.game_mode == 'pvp':
            if self.board.undo_last_move(): self.current_player_color *= -1; self._redraw_board()
        elif self.game_mode == 'ai':
            if len(self.board.history) >= 2:
                self.board.undo_last_move(); self.board.undo_last_move(); self._redraw_board()
            elif len(self.board.history) == 1:
                self.board.undo_last_move(); self._redraw_board()

    # [關鍵修改] 支援多種主題的繪圖函式
    def _redraw_board(self, update=True):
        
        # 1. 繪製背景 (根據主題)
        if self.current_theme == 'Classic':
            self.screen.blit(self.img_bg, (0, 0))
        elif self.current_theme == 'Dark':
            self.screen.fill((30, 30, 35)) # 深灰背景
            # 畫網格 (霓虹風)
            grid_color = (60, 60, 70)
            for i in range(LEVEL):
                start = 25 + i * 50
                pygame.draw.line(self.screen, grid_color, (25, start), (725, start), 2)
                pygame.draw.line(self.screen, grid_color, (start, 25), (start, 725), 2)
            # 畫星位
            for x in [3, 7, 11]:
                for y in [3, 7, 11]:
                    pos = (25 + x*50, 25 + y*50)
                    pygame.draw.circle(self.screen, grid_color, pos, 5)
                    
        elif self.current_theme == 'Paper':
            self.screen.fill((245, 240, 230)) # 米色紙張背景
            # 畫網格 (鉛筆風)
            grid_color = (100, 100, 120)
            for i in range(LEVEL):
                start = 25 + i * 50
                pygame.draw.line(self.screen, grid_color, (25, start), (725, start), 1)
                pygame.draw.line(self.screen, grid_color, (start, 25), (start, 725), 1)

        # 2. 繪製棋子
        for x in range(LEVEL):
            for y in range(LEVEL):
                color = self.board.grid[x][y]
                if color == 0: continue
                
                center = (25 + x * 50, 25 + y * 50)
                
                if self.current_theme == 'Classic':
                    img = self.img_black if color == 1 else self.img_white
                    # img 座標要扣掉 offset
                    pos = (center[0] - img.get_width()/2, center[1] - img.get_height()/2)
                    self.screen.blit(img, pos)
                    
                elif self.current_theme == 'Dark':
                    # 黑棋=螢光青(Cyan), 白棋=螢光紅(Magenta)
                    c = (0, 255, 255) if color == 1 else (255, 0, 100)
                    pygame.draw.circle(self.screen, c, center, 20)
                    pygame.draw.circle(self.screen, (255, 255, 255), center, 22, 2) # 光暈邊框
                    
                elif self.current_theme == 'Paper':
                    # 黑棋=實心深灰, 白棋=空心圓
                    if color == 1:
                        pygame.draw.circle(self.screen, (50, 50, 50), center, 18)
                    else:
                        pygame.draw.circle(self.screen, (50, 50, 50), center, 18, 2)
                        pygame.draw.circle(self.screen, (255, 255, 255), center, 16)

        # 3. 繪製 Ghost (預覽)
        if self.ghost_pos:
            gx, gy = self.ghost_pos
            center = (25 + gx * 50, 25 + gy * 50)
            
            if self.current_theme == 'Classic':
                img = self.img_black_ghost if self.current_player_color == 1 else self.img_white_ghost
                pos = (center[0] - img.get_width()/2, center[1] - img.get_height()/2)
                self.screen.blit(img, pos)
            else:
                # 程式繪圖的 Ghost
                ghost_color = (0, 255, 255) if self.current_player_color == 1 else (255, 0, 100)
                if self.current_theme == 'Paper': ghost_color = (150, 150, 150)
                
                # 畫一個半透明圓圈 (Pygame draw circle 不支援 alpha，畫空心代替)
                pygame.draw.circle(self.screen, ghost_color, center, 20, 1)

        # 4. 繪製最後一手 (Last Move)
        if self.rule_length != 'go' and self.board.history:
            lx, ly = self.board.history[-1]
            center = (25 + lx * 50, 25 + ly * 50)
            mark_color = (220, 50, 50) # 紅點
            if self.current_theme == 'Dark': mark_color = (255, 255, 0) # 黃點
            pygame.draw.circle(self.screen, mark_color, center, 5)

        # 5. 繪製提示 (Hint)
        if self.hint_pos:
            hx, hy = self.hint_pos
            center = (25 + hx * 50, 25 + hy * 50)
            pygame.draw.circle(self.screen, (255, 50, 50), center, 22, 3)

        if update:
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
        self.sound_move.play()
        self.board.grid = self.go_engine.grid
        self._redraw_board()
        self.current_player_color *= -1

    def _execute_move(self, m, n, color):
        self.hint_pos = None 
        self.ghost_pos = None 
        self.board.place_stone(m, n, color)
        self._redraw_board()
        
        if self.board.check_win(m, n, color):
            self.game_over = True
            self.winner = color
            if self.game_mode == 'pvp': self.sound_win.play()
            else:
                if color == 1: self.sound_win.play()
                else: self.sound_loss.play()
            self._redraw_board()
            return 

        if self.board.is_full():
            self.game_over = True
            self.winner = 0
            self.sound_loss.play()
            self._redraw_board()
            return

        self.sound_move.play()
        if self.game_mode == 'pvp': self.current_player_color *= -1

    def _trigger_ai_move(self):
        if self.rule_length == 'go': return
        ai_color = -1 
        x, y = self.ai.get_move(self.board.grid, ai_color)
        self._execute_move(x, y, ai_color)

    def _show_hint(self):
        if self.rule_length == 'go': return
        self.hint_ai.ai_move_count = 100 
        x, y = self.hint_ai.get_move(self.board.grid, -1, -1, self.current_player_color)
        self.hint_pos = (x, y)
        self._redraw_board()

if __name__ == "__main__":
    game = GomokuGame()
    game.run()