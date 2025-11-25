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
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
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
        print("Game Over. Waiting for 'R'...")
        
        # Determine Result Text
        if self.rule_length == 'go':
            # Use the detailed score string generated in _end_go_game
            win_text = self.final_score_text
            win_color = (255, 215, 0) # Gold color for Go results
        else:
            # Standard Gomoku/Connect4 Win Text
            if self.winner == 1:
                win_text = "Black Win the game"
                win_color = (50, 200, 50) 
            elif self.winner == -1:
                win_text = "White (AI) Win the game"
                win_color = (220, 50, 50)
            else:
                win_text = "Draw Game"
                win_color = (200, 200, 200)

        prompt_text = "Press 'R' to return to Menu"
        prompt_color = (255, 255, 255)

        surf_win = self.font_m.render(win_text, True, win_color)
        surf_prompt = self.font_s.render(prompt_text, True, prompt_color)
        
        vertical_padding = 25
        total_text_height = surf_win.get_height() + surf_prompt.get_height()
        w = max(surf_win.get_width(), surf_prompt.get_width()) + 80
        h = total_text_height + (vertical_padding * 2)
        
        overlay = pygame.Surface((w, h))
        overlay.fill((40, 40, 40)) 
        overlay.set_alpha(230)    
        
        center_x = SCREEN_WIDTH // 2
        center_y = SCREEN_HEIGHT // 2
        overlay_rect = overlay.get_rect(center=(center_x, center_y))
        
        waiting = True
        while waiting:
            pygame.time.Clock().tick(30)
            self.screen.blit(overlay, overlay_rect)
            
            win_rect = surf_win.get_rect(midtop=(center_x, overlay_rect.top + vertical_padding))
            prompt_rect = surf_prompt.get_rect(midtop=(center_x, win_rect.bottom))
            
            self.screen.blit(surf_win, win_rect)
            self.screen.blit(surf_prompt, prompt_rect)
            pygame.display.update()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False; waiting = False; return
                if event.type == KEYDOWN and event.key == K_r:
                    waiting = False; return

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
                if event.key == K_r:
                    self.force_quit_to_menu = True; self.game_over = True; return
                
                # [NEW] 'P' to Pass (Only in Go Mode)
                if event.key == K_p and self.rule_length == 'go' and not self.game_over:
                    self._handle_go_pass()
                    
                if event.key == K_u and not self.game_over: self._undo_move()
                if event.key == K_h and not self.game_over: self._show_hint()

            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                if self.game_mode == 'ai' and self.current_player_color == -1: continue 
                self._handle_mouse_click(event.pos)

    def _handle_go_pass(self):
        """Handles passing logic for Go."""
        print(f"Player {self.current_player_color} Passed!")
        self.pass_count += 1
        self.current_player_color *= -1
        
        # Show "Pass" message temporarily (optional enhancement)
        
        if self.pass_count >= 2:
            self._end_go_game()

    def _end_go_game(self):
        """Calculates scores and ends the Go game."""
        print("Both passed. Calculating score...")
        black_score, white_score = self.go_engine.calculate_score()
        
        # Standard Komi (Compensation for White) is usually 6.5 or 7.5.
        # We will skip Komi for simplicity, or you can add it:
        # white_score += 6.5
        
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
        if self.rule_length == 'go':
            print("Undo not supported in Go mode yet.")
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
        for x in range(LEVEL):
            for y in range(LEVEL):
                color = self.board.grid[x][y]
                if color != 0:
                    stone_img = self.img_black if color == 1 else self.img_white
                    self.screen.blit(stone_img, self.dot_list[LEVEL * x + y])
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
        # Placing a stone resets the pass count
        self.pass_count = 0
        
        success, captures = self.go_engine.place_stone(m, n, color)
        
        if not success:
            print("Invalid Move (Suicide or Occupied)")
            return 

        if captures:
            print(f"Captured {len(captures)} stones!")

        self._redraw_board()
        self.current_player_color *= -1

    def _execute_move(self, m, n, color):
        self.hint_pos = None 
        self.board.place_stone(m, n, color)
        self._redraw_board()
        
        if self.board.check_win(m, n, color):
            self.game_over = True; self.winner = color; return
        if self.board.is_full():
            self.game_over = True; self.winner = 0; return
        if self.game_mode == 'pvp':
            self.current_player_color *= -1

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