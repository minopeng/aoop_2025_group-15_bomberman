import pygame
from pygame.locals import *
from time import sleep
import os
import sys
import threading

# --- Custom Module Imports ---
from constants import *
from game_board import GameBoard
from rl_ai_player import RL_AIPlayer   
from start_menu import StartMenu
from ai_player import AIPlayer
from go_engine import GoEngine
from network import NetworkManager

class GomokuGame:
    def __init__(self):
        # [Fix 1] Audio pre-init to prevent crash
        try:
            pygame.mixer.pre_init(44100, -16, 2, 512)
        except Exception as e:
            print(f"Warning: Mixer pre_init failed: {e}")

        pygame.init()
        
        try:
            pygame.mixer.init()
        except:
            pass

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption("Board Game AI Arena")
        
        self.font_m = pygame.font.SysFont("黑体", 40)
        self.font_l = pygame.font.SysFont("黑体", 60)
        self.font_s = pygame.font.SysFont("黑体", 30)
        
        # [Fix 2] Initialize sound variables to None
        self.sound_move = None
        self.sound_win = None
        self.sound_loss = None

        try:
            # --- Load Images ---
            self.img_bg = pygame.image.load('./Res/bg.png').convert()
            img_white = pygame.image.load('./Res/white.png').convert_alpha()
            img_black = pygame.image.load('./Res/black.png').convert_alpha()
            
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
            
            self.img_white_ghost = self.img_white.copy(); self.img_white_ghost.set_alpha(128)
            self.img_black_ghost = self.img_black.copy(); self.img_black_ghost.set_alpha(128)

            # --- Load Sounds (Safe Mode) ---
            if os.path.exists('./Res/drop.wav'):
                self.sound_move = pygame.mixer.Sound('./Res/drop.wav')
                self.sound_move.set_volume(0.8)
            else: print("⚠️ Warning: drop.wav not found!")

            if os.path.exists('./Res/win.wav'):
                self.sound_win = pygame.mixer.Sound('./Res/win.wav')
                self.sound_win.set_volume(1.0)
            else: print("⚠️ Warning: win.wav not found!")

            if os.path.exists('./Res/loss.wav'):
                self.sound_loss = pygame.mixer.Sound('./Res/loss.wav')
                self.sound_loss.set_volume(1.0)
            else: print("⚠️ Warning: loss.wav not found!")
            
        except pygame.error as e:
            print(f"❌ Error loading resources: {e}")

        self.board = GameBoard()
        self.menu = StartMenu(self.screen, self.img_bg, self.font_l, self.font_s)
        self.ai = None; self.hint_ai = None; self.go_engine = None; self.network = None
        
        self.game_mode = None; self.rule_length = 5; self.current_theme = 'Classic'
        self.running = True
        self.game_over = False; self.force_quit_to_menu = False 
        self.winner = 0; self.current_player_color = 1 
        self.my_network_color = 0 
        
        self.pass_count = 0; self.final_score_text = "" 
        self.dot_list = [(25 + i * 50, 25 + j * 50) for i in range(LEVEL) for j in range(LEVEL)]
        self.hint_pos = None; self.ghost_pos = None 

    # [Fix 3] Safe Volume Update
    def update_volume(self, vol):
        try:
            if vol is None: vol = 0.8
            vol = float(vol)
            vol = max(0.0, min(1.0, vol))
            
            if self.sound_move: self.sound_move.set_volume(vol)
            if self.sound_win: self.sound_win.set_volume(vol)
            if self.sound_loss: self.sound_loss.set_volume(vol)
        except Exception as e:
            print(f"Volume Update Error: {e}")

    def run(self):
        while self.running:
            # 1. Get Menu Result (Safe Unpacking)
            menu_result = self.menu.run()
            
            vol = 0.8 # Default
            if menu_result is None or len(menu_result) == 0:
                self.running = False; break
                
            if len(menu_result) == 4:
                mode, length, theme, vol = menu_result
            elif len(menu_result) == 3:
                mode, length, theme = menu_result
            else:
                self.running = False; break

            if mode is None: self.running = False; break

            # Apply Settings
            self.game_mode = mode
            self.rule_length = length
            self.current_theme = theme
            self.update_volume(vol)
            
            self.network = None 
            self.my_network_color = 0
            
            # 2. Network Setup
            if mode == 'lan_host':
                if not self._setup_host(): continue 
            elif mode == 'lan_join':
                if not self._setup_client(): continue
            
            # 3. Load AI
            if mode == 'ai':
                if length == 'go': self.game_mode = 'pvp'
                else: self._load_ai_model(length)
            
            if length != 'go': self.hint_ai = AIPlayer(target_length=self.rule_length)
            
            # 4. Start Game
            print(f"\n--- 🎮 Starting: {mode} | Rule: {self.rule_length} | Theme: {self.current_theme} ---")
            self._reset_game_state()
            self._play_match()
            
            # 5. Cleanup
            if self.network: self.network.close()
            
            if self.force_quit_to_menu:
                self.force_quit_to_menu = False 
                continue

            if self.running: self._wait_for_menu_input()

        pygame.quit(); sys.exit()

    def _setup_host(self):
        self.network = NetworkManager()
        self.network.create_server()
        local_ip = self.network.get_local_ip()
        
        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == QUIT: pygame.quit(); sys.exit()
                if event.type == KEYDOWN and event.key == K_ESCAPE: 
                    self.network.close(); return False

            self.screen.fill((30, 30, 30))
            txt1 = self.font_m.render(f"Host Created!", True, (0, 255, 0))
            txt2 = self.font_m.render(f"Your IP: {local_ip}", True, (255, 255, 255))
            txt3 = self.font_s.render("Waiting for opponent... (ESC to Cancel)", True, (150, 150, 150))
            
            cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
            self.screen.blit(txt1, txt1.get_rect(center=(cx, cy-50)))
            self.screen.blit(txt2, txt2.get_rect(center=(cx, cy)))
            self.screen.blit(txt3, txt3.get_rect(center=(cx, cy+60)))
            pygame.display.update()
            
            if self.network.wait_for_connection():
                config_str = f"SETUP:{self.rule_length},{self.current_theme}"
                self.network.send(config_str)
                self.my_network_color = 1 
                return True
        return False

    def _setup_client(self):
        user_text = ''; input_active = True; clock = pygame.time.Clock()
        while input_active:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == QUIT: pygame.quit(); sys.exit()
                if event.type == KEYDOWN:
                    if event.key == K_RETURN: input_active = False
                    elif event.key == K_BACKSPACE: user_text = user_text[:-1]
                    elif event.key == K_ESCAPE: return False
                    else: 
                        if len(user_text) < 15: user_text += event.unicode
            self.screen.fill((30, 30, 30))
            txt_title = self.font_m.render("Enter Host IP:", True, (0, 255, 0))
            self.screen.blit(txt_title, txt_title.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 - 50)))
            input_box = pygame.Rect(SCREEN_WIDTH//2 - 150, SCREEN_HEIGHT//2, 300, 50)
            pygame.draw.rect(self.screen, (255, 255, 255), input_box, 2)
            self.screen.blit(self.font_m.render(user_text, True, (255, 255, 255)), (input_box.x+10, input_box.y+5))
            txt_hint = self.font_s.render("Press ENTER to Connect", True, (150, 150, 150))
            self.screen.blit(txt_hint, txt_hint.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 80)))
            pygame.display.update()

        target_ip = user_text.strip()
        if not target_ip: target_ip = "127.0.0.1" 
        
        self.network = NetworkManager()
        if self.network.connect_to_server(target_ip):
            self.my_network_color = -1 
            while self.network.connected:
                if self.network.received_data and self.network.received_data.startswith("SETUP:"):
                    data_str = self.network.received_data.split(":")[1]
                    parts = data_str.split(',')
                    if parts[0] == 'go': self.rule_length = 'go'
                    else: self.rule_length = int(parts[0])
                    if len(parts) > 1: self.current_theme = parts[1]
                    self.network.received_data = None
                    return True
                pygame.time.wait(50)
        return False

    def _load_ai_model(self, length):
        if length == 'go': return 
        model_path = ""
        if length == 4: model_path = "models/connect4_graduation.keras"
        elif length == 5: model_path = "models/gomoku_rl_model_final.keras"
        elif length == 6: model_path = "models/connect6_rl_model_latest.keras"

        if os.path.exists(model_path):
            try:
                self.ai = RL_AIPlayer(model_path=model_path)
            except Exception as e:
                print(f"Error loading AI: {e}")
                self.ai = RL_AIPlayer()
        else:
            self.ai = RL_AIPlayer() 

    def _reset_game_state(self):
        t_len = 5 if self.rule_length == 'go' else self.rule_length
        self.board = GameBoard(target_length=t_len)
        if self.rule_length == 'go':
            self.go_engine = GoEngine(self.board.grid)
            self.pass_count = 0; self.final_score_text = ""
        self.game_over = False; self.force_quit_to_menu = False 
        self.winner = 0; self.current_player_color = 1 
        self.hint_pos = None; self.ghost_pos = None 
        self._redraw_board()

    def _play_match(self):
        while not self.game_over:
            self._handle_events()
            # Network Logic
            if self.game_mode in ['lan_host', 'lan_join']:
                if self.current_player_color != self.my_network_color:
                    if self.network and self.network.received_data:
                        data = self.network.received_data
                        self.network.received_data = None
                        if data == "PASS": self._handle_go_pass()
                        else:
                            try:
                                parts = data.split(',')
                                r_x, r_y = int(parts[0]), int(parts[1])
                                if self.rule_length == 'go': self._execute_go_move(r_x, r_y, self.current_player_color)
                                else: self._execute_move(r_x, r_y, self.current_player_color)
                            except: pass
            
            # AI Logic (Local)
            if self.game_mode == 'ai' and self.current_player_color == -1: pass
    
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: pygame.quit(); sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_r: self.force_quit_to_menu = True; self.game_over = True; return
                
                is_net = self.game_mode in ['lan_host', 'lan_join']
                if event.key == K_p and self.rule_length == 'go' and not self.game_over: 
                    if is_net and self.current_player_color != self.my_network_color: return
                    self._handle_go_pass()
                    if is_net: self.network.send("PASS") 

                if event.key == K_u and not self.game_over and not is_net: self._undo_move()
                if event.key == K_h and not self.game_over: self._show_hint()

            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                if self.game_mode in ['lan_host', 'lan_join']:
                    if self.current_player_color != self.my_network_color: continue
                if self.game_mode == 'ai' and self.current_player_color == -1: continue 
                self._handle_mouse_click(event.pos)

            if event.type == MOUSEMOTION and not self.game_over:
                if self.game_mode in ['lan_host', 'lan_join'] and self.current_player_color != self.my_network_color: 
                    if self.ghost_pos: self.ghost_pos = None; self._redraw_board()
                    continue
                if self.game_mode == 'ai' and self.current_player_color == -1:
                    if self.ghost_pos: self.ghost_pos = None; self._redraw_board()
                    continue
                self._update_ghost_pos(event.pos)

    def _update_ghost_pos(self, pos):
        x, y = pos
        if not (25 <= x <= 725 and 25 <= y <= 725):
            if self.ghost_pos: self.ghost_pos = None; self._redraw_board(); return
        m = int(round((x - 25) / 50)); n = int(round((y - 25) / 50))
        is_valid = False
        if self.rule_length == 'go':
            if 0 <= m < LEVEL and 0 <= n < LEVEL and self.board.grid[m][n] == 0: is_valid = True
        else:
            if self.board.is_valid(m, n) and self.board.is_empty(m, n): is_valid = True
        new_ghost = (m, n) if is_valid else None
        if new_ghost != self.ghost_pos: self.ghost_pos = new_ghost; self._redraw_board()

    # [Fix 4] Re-added missing _handle_mouse_click
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
            
            # Send Network Move
            if self.game_mode in ['lan_host', 'lan_join']:
                self.network.send(f"{m},{n}")

            if self.game_mode == 'ai' and not self.game_over:
                pygame.display.update(); sleep(0.1); self._trigger_ai_move()

    def _handle_go_pass(self):
        self.pass_count += 1
        self.current_player_color *= -1
        if self.pass_count >= 2: self._end_go_game()

    def _end_go_game(self):
        b_s, w_s = self.go_engine.calculate_score()
        if b_s > w_s: self.winner = 1; self.final_score_text = f"Black Wins! ({b_s}:{w_s})"
        elif w_s > b_s: self.winner = -1; self.final_score_text = f"White Wins! ({w_s}:{b_s})"
        else: self.winner = 0; self.final_score_text = f"Draw! ({b_s})"
        self._play_end_sound(self.winner)
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

    def _play_sound_safe(self, sound_obj):
        try:
            if sound_obj: sound_obj.play()
        except: pass

    def _play_end_sound(self, winner_color):
        if self.game_mode == 'pvp':
            if winner_color != 0: self._play_sound_safe(self.sound_win)
            else: self._play_sound_safe(self.sound_loss)
            return
        if self.game_mode == 'ai':
            if winner_color == 1: self._play_sound_safe(self.sound_win)
            else: self._play_sound_safe(self.sound_loss)
            return
        if self.game_mode in ['lan_host', 'lan_join']:
            if winner_color == 0: self._play_sound_safe(self.sound_loss)
            elif winner_color == self.my_network_color: self._play_sound_safe(self.sound_win)
            else: self._play_sound_safe(self.sound_loss)

    def _execute_go_move(self, m, n, color):
        self.pass_count = 0
        success, captures = self.go_engine.place_stone(m, n, color)
        if not success: return 
        if self.game_mode in ['lan_host', 'lan_join'] and color == self.my_network_color:
            self.network.send(f"{m},{n}")
        self._play_sound_safe(self.sound_move)
        self.board.grid = self.go_engine.grid
        self._redraw_board()
        self.current_player_color *= -1

    def _execute_move(self, m, n, color):
        self.hint_pos = None; self.ghost_pos = None 
        self.board.place_stone(m, n, color)
        self._redraw_board()
        
        if self.board.check_win(m, n, color):
            self.game_over = True; self.winner = color
            self._play_end_sound(color)
            self._redraw_board(); return 

        if self.board.is_full():
            self.game_over = True; self.winner = 0
            self._play_end_sound(0)
            self._redraw_board(); return

        self._play_sound_safe(self.sound_move)
        if self.game_mode in ['pvp', 'lan_host', 'lan_join']:
            self.current_player_color *= -1
        
        
        
        self._redraw_board()

    def _trigger_ai_move(self):
        if self.rule_length == 'go': return
        ai_color = -1 
        x, y = self.ai.get_move(self.board.grid, ai_color)
        self._execute_move(x, y, ai_color)

    def _show_hint(self):
        if self.rule_length == 'go': return
        self.hint_ai.ai_move_count = 100 
        x, y = self.hint_ai.get_move(self.board.grid, -1, -1, self.current_player_color)
        self.hint_pos = (x, y); self._redraw_board()

    def _redraw_board(self, update=True):
        if self.current_theme == 'Classic': self.screen.blit(self.img_bg, (0, 0)); grid_c = None
        elif self.current_theme == 'Dark':
            self.screen.fill((30, 30, 35)); grid_c = (60, 60, 70)
        elif self.current_theme == 'Paper':
            self.screen.fill((245, 240, 230)); grid_c = (100, 100, 120)
        elif self.current_theme == 'Ocean':
            self.screen.fill((20, 40, 60)); grid_c = (100, 200, 200)
        elif self.current_theme == 'Matrix':
            self.screen.fill((0, 20, 0)); grid_c = (0, 150, 0)
        elif self.current_theme == 'Pink':
            self.screen.fill((255, 240, 245)); grid_c = (219, 112, 147)

        if grid_c:
            for i in range(LEVEL):
                s = 25 + i * 50
                pygame.draw.line(self.screen, grid_c, (25, s), (725, s), 1 if self.current_theme=='Paper' else 2)
                pygame.draw.line(self.screen, grid_c, (s, 25), (s, 725), 1 if self.current_theme=='Paper' else 2)
            for x in [3, 7, 11]:
                for y in [3, 7, 11]: pygame.draw.circle(self.screen, grid_c, (25+x*50, 25+y*50), 5)

        for x in range(LEVEL):
            for y in range(LEVEL):
                color = self.board.grid[x][y]
                if color == 0: continue
                center = (25 + x * 50, 25 + y * 50)
                if self.current_theme == 'Classic':
                    img = self.img_black if color == 1 else self.img_white
                    self.screen.blit(img, (center[0]-img.get_width()/2, center[1]-img.get_height()/2))
                elif self.current_theme == 'Dark':
                    c = (0, 255, 255) if color == 1 else (255, 0, 100)
                    pygame.draw.circle(self.screen, c, center, 20)
                    pygame.draw.circle(self.screen, (255, 255, 255), center, 22, 2)
                elif self.current_theme == 'Ocean':
                    c = (20, 20, 30) if color == 1 else (200, 220, 255)
                    pygame.draw.circle(self.screen, c, center, 20)
                    pygame.draw.circle(self.screen, (100, 150, 200), center, 21, 1)
                elif self.current_theme == 'Matrix':
                    c = (0, 255, 0) if color == 1 else (0, 50, 0)
                    pygame.draw.circle(self.screen, c, center, 18, 0 if color==1 else 2)
                    if color == 1: pygame.draw.circle(self.screen, (200, 255, 200), center, 10)
                elif self.current_theme == 'Pink':
                    c = (50, 50, 50) if color == 1 else (255, 255, 255)
                    pygame.draw.circle(self.screen, c, center, 20)
                    pygame.draw.circle(self.screen, (255, 105, 180), center, 21, 2)
                elif self.current_theme == 'Paper':
                    if color == 1: pygame.draw.circle(self.screen, (50, 50, 50), center, 18)
                    else: pygame.draw.circle(self.screen, (50, 50, 50), center, 18, 2); pygame.draw.circle(self.screen, (255, 255, 255), center, 16)

        if self.ghost_pos:
            gx, gy = self.ghost_pos; center = (25 + gx * 50, 25 + gy * 50)
            if self.current_theme == 'Classic':
                img = self.img_black_ghost if self.current_player_color == 1 else self.img_white_ghost
                self.screen.blit(img, (center[0]-img.get_width()/2, center[1]-img.get_height()/2))
            else:
                gc = (100, 100, 100)
                if self.current_theme == 'Dark': gc = (0, 255, 255) if self.current_player_color == 1 else (255, 0, 100)
                elif self.current_theme == 'Matrix': gc = (0, 200, 0)
                pygame.draw.circle(self.screen, gc, center, 20, 1)

        if self.rule_length != 'go' and self.board.history:
            lx, ly = self.board.history[-1]; center = (25 + lx * 50, 25 + ly * 50)
            mc = (220, 50, 50) if self.current_theme != 'Dark' else (255, 255, 0)
            pygame.draw.circle(self.screen, mc, center, 5)

        if self.hint_pos:
            hx, hy = self.hint_pos; center = (25 + hx * 50, 25 + hy * 50)
            pygame.draw.circle(self.screen, (255, 50, 50), center, 22, 3)
            
        if update: pygame.display.update()

    def _prepare_replay_data(self):
        if self.rule_length == 'go': return [] 
        replay_data = []
        for (x, y) in self.board.history:
            replay_data.append((x, y, self.board.grid[x][y]))
        return replay_data

    def _wait_for_menu_input(self):
        full_replay_history = self._prepare_replay_data()
        current_step = len(full_replay_history); max_step = len(full_replay_history)
        is_replaying = False 
        
        win_text = ""; win_color = (255, 255, 255)
        if self.game_mode in ['lan_host', 'lan_join']:
            if self.winner == self.my_network_color: win_text = "YOU WIN!"; win_color = (0, 255, 0)
            elif self.winner == 0: win_text = "DRAW!"; win_color = (200, 200, 200)
            else: win_text = "YOU LOSE..."; win_color = (255, 0, 0)
        elif self.game_mode == 'ai':
            if self.winner == 1: win_text = "YOU WIN!"; win_color = (0, 255, 0)
            elif self.winner == -1: win_text = "AI WINS"; win_color = (255, 0, 0)
            else: win_text = "DRAW"; win_color = (200, 200, 200)
        else: 
            if self.winner == 1: win_text = "BLACK WINS"; win_color = (50, 200, 50)
            elif self.winner == -1: win_text = "WHITE WINS"; win_color = (200, 50, 50)
            else: win_text = "DRAW"; win_color = (200, 200, 200)

        if self.rule_length == 'go': win_text = self.final_score_text; win_color = (255, 215, 0)

        prompt_text = "Press 'R' to Menu"; replay_hint_text = "Replay: [<-] Back | [->] Fwd"
        alpha = 0; scale = 1.0; scale_dir = 0.01 
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT)); overlay.fill((20, 20, 20)) 
        
        clock = pygame.time.Clock()
        waiting = True; self.ghost_pos = None
    
        while waiting:
            clock.tick(60); self._redraw_board(update=False)
            for event in pygame.event.get():
                if event.type == QUIT: self.running = False; waiting = False; return
                if event.type == KEYDOWN:
                    if event.key == K_r: waiting = False; return
                    if event.key == K_LEFT:
                        if self.rule_length == 'go':
                            if self.go_engine.undo(): is_replaying = True
                        else:
                            if current_step > 0: self.board.undo_last_move(); current_step -= 1; is_replaying = True
                    if event.key == K_RIGHT:
                        if self.rule_length != 'go' and current_step < max_step:
                            nx, ny, nc = full_replay_history[current_step]
                            self.board.place_stone(nx, ny, nc)
                            current_step += 1; is_replaying = True; self._play_sound_safe(self.sound_move)

            target_alpha = 100 if is_replaying else 180 
            if alpha < target_alpha: alpha += 2 
            elif alpha > target_alpha: alpha -= 5
            overlay.set_alpha(alpha)
            
            scale += scale_dir
            if scale > 1.05 or scale < 0.95: scale_dir *= -1
            self.screen.blit(overlay, (0, 0)); cx, cy = SCREEN_WIDTH//2, SCREEN_HEIGHT//2
            
            if is_replaying:
                surf_step = self.font_m.render(f"Step: {current_step} / {max_step}", True, (100, 200, 255))
                self.screen.blit(surf_step, surf_step.get_rect(center=(cx, 50)))
                surf_hint = self.font_s.render(replay_hint_text, True, (200, 200, 200))
                self.screen.blit(surf_hint, surf_hint.get_rect(center=(cx, SCREEN_HEIGHT - 80)))
                surf_ret = self.font_s.render(prompt_text, True, (150, 150, 150))
                self.screen.blit(surf_ret, surf_ret.get_rect(center=(cx, SCREEN_HEIGHT - 40)))
            else:
                surf_win = self.font_l.render(win_text, True, win_color)
                w, h = int(surf_win.get_width() * scale), int(surf_win.get_height() * scale)
                scaled_win = pygame.transform.smoothscale(surf_win, (w, h))
                self.screen.blit(scaled_win, scaled_win.get_rect(center=(cx, cy - 30)))
                
                shadow = self.font_l.render(win_text, True, (0, 0, 0))
                scaled_shadow = pygame.transform.smoothscale(shadow, (w, h))
                self.screen.blit(scaled_shadow, scaled_shadow.get_rect(center=(cx+3, cy-27)))

                if pygame.time.get_ticks() % 2000 < 1000:
                    surf_rep = self.font_s.render(replay_hint_text, True, (150, 150, 150))
                    self.screen.blit(surf_rep, surf_rep.get_rect(center=(cx, cy + 40)))
                if pygame.time.get_ticks() % 1500 < 800: 
                    surf_pmt = self.font_s.render(prompt_text, True, (200, 200, 200))
                    self.screen.blit(surf_pmt, surf_pmt.get_rect(center=(cx, cy + 80)))
            
            pygame.display.update()

if __name__ == "__main__":
    game = GomokuGame()
    game.run()