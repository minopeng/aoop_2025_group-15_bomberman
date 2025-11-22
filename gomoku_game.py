import pygame
from pygame.locals import *
from time import sleep
import os

# Imports
from constants import *
from game_board import GameBoard
from rl_ai_player import RL_AIPlayer   
from start_menu import StartMenu
from game_over_screen import GameOverScreen

class GomokuGame:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), 0, 32)
        pygame.display.set_caption("Gomoku RL AI Test") # Translated Caption
        
        # CHANGED: Used 'arial' instead of 'SimHei' (Chinese font)
        self.font_m = pygame.font.SysFont("arial", 40)
        self.font_l = pygame.font.SysFont("arial", 60, bold=True)
        self.font_s = pygame.font.SysFont("arial", 30)
        
        # Load Images
        try:
            self.img_bg = pygame.image.load('./Res/bg.png').convert()
            img_white = pygame.image.load('./Res/white.png').convert_alpha()
            img_black = pygame.image.load('./Res/black.png').convert_alpha()
            self.img_white = pygame.transform.smoothscale(img_white, (int(img_white.get_width() * 1.5), int(img_white.get_height() * 1.5)))
            self.img_black = pygame.transform.smoothscale(img_black, (int(img_black.get_width() * 1.5), int(img_black.get_height() * 1.5)))
        except pygame.error as e:
            print(f"Error: Image resources not found - {e}")
            exit()

        # Load AI
        MODEL_FILE_TO_TEST = "models/gomoku_rl_model_final.keras"
        print(f"--- Loading AI Model: {MODEL_FILE_TO_TEST} ---")
        
        if not os.path.exists(MODEL_FILE_TO_TEST):
            print(f"❌ Error: Model file not found!")
            exit()
            
        try:
            self.ai = RL_AIPlayer(model_path=MODEL_FILE_TO_TEST)
            print("✅ Model loaded successfully!")
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            exit()

        # Initialize Screens
        self.menu = StartMenu(self.screen, self.img_bg, self.font_l, self.font_s)
        self.game_over_screen = GameOverScreen(self.screen, self.font_l, self.font_s)
        
        # Game State Variables
        self.board = None
        self.game_mode = None 
        self.game_over = False
        self.winner = 0 # 0: Draw, 1: Black, -1: White
        self.current_player_color = 1 
        self.dot_list = [(25 + i * 50 - self.img_white.get_width() / 2, 25 + j * 50 - self.img_white.get_height() / 2) 
                         for i in range(LEVEL) for j in range(LEVEL)]

    def run(self):
        """Main Game Loop: Manages the flow between Menu, Game, and GameOver"""
        while True:
            # --- 1. Show Start Menu ---
            self.game_mode = self.menu.run()
            if self.game_mode is None:
                break # User clicked Quit in Menu

            # --- 2. Game Loop (Repeats if 'Restart' is chosen) ---
            while True: 
                self._reset_game_state()
                
                # Run the actual gameplay
                self._play_match()
                
                # --- 3. Show Game Over Screen ---
                # Returns: 'restart', 'menu', or None
                action = self.game_over_screen.run(self.winner)
                
                if action == 'restart':
                    continue # Loop back to _reset_game_state()
                elif action == 'menu':
                    break # Break inner loop, go back to Start Menu
                else:
                    pygame.quit()
                    exit() # Quit entirely

        pygame.quit()
        exit()

    def _reset_game_state(self):
        """Resets board and variables for a new match"""
        self.board = GameBoard()
        self.game_over = False
        self.winner = 0
        self.current_player_color = 1
        self.screen.blit(self.img_bg, (0, 0))
        pygame.display.update()

    def _play_match(self):
        """The core loop for placing stones until someone wins"""
        while not self.game_over:
            self._handle_events()
            
            # Small delay to prevent CPU hogging
            if self.game_mode == 'ai' and self.current_player_color == -1 and not self.game_over:
                 pass

    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT: 
                pygame.quit()
                exit()
            if event.type == MOUSEBUTTONDOWN and not self.game_over:
                # Only human (Black=1) can click. 
                if self.game_mode == 'ai' and self.current_player_color == -1:
                    continue # Ignore clicks during AI turn
                self._handle_mouse_click(event.pos)

    def _handle_mouse_click(self, pos):
        x, y = pos
        if not (25 <= x <= 725 and 25 <= y <= 725): return
        m = int(round((x - 25) / 50))
        n = int(round((y - 25) / 50))
        if not self.board.is_valid(m, n): return
        if not self.board.is_empty(m, n): return

        # Execute Human Move
        self._execute_move(m, n, self.current_player_color)
        
        if self.game_over: return

        # Trigger AI if needed
        if self.game_mode == 'ai' and not self.game_over:
            pygame.display.update()
            # sleep(0.1) 
            self._trigger_ai_move()

    def _execute_move(self, m, n, color):
        self.board.place_stone(m, n, color)
        stone_img = self.img_black if color == 1 else self.img_white
        self.screen.blit(stone_img, self.dot_list[LEVEL * m + n])
        pygame.display.update()
        
        # Check Win
        if self.board.check_win(m, n, color):
            self.game_over = True
            self.winner = color
            return
        
        # Check Draw
        if self.board.is_full():
            self.game_over = True
            self.winner = 0
            return
            
        # Switch Turn
        if self.game_mode == 'pvp':
            self.current_player_color *= -1

    def _trigger_ai_move(self):
        ai_color = -1 
        x, y = self.ai.get_move(self.board.grid, ai_color)
        
        if not (self.board.is_valid(x, y) and self.board.is_empty(x, y)):
            print("⚠️ AI Error: Invalid move, choosing random spot.")
            x, y = self.ai._find_random_empty(self.board.grid)
        
        self._execute_move(x, y, ai_color)