# start_menu.py
import pygame
from pygame.locals import *
from constants import SCREEN_WIDTH
from ui import Button

class StartMenu:
    def __init__(self, screen, background_img, font_title, font_button):
        self.screen = screen
        self.background_img = background_img
        self.font_button = font_button
        
        # Initial Mode
        self.current_rule = 5 # Default to Gomoku
        
        # Colors
        BUTTON_COLOR = (70, 130, 180)
        BUTTON_HOVER = (100, 149, 237)
        MODE_COLOR   = (46, 139, 87)  # Sea Green
        MODE_HOVER   = (60, 179, 113)
        QUIT_COLOR   = (205, 92, 92)
        QUIT_HOVER   = (255, 99, 71)
        
        self.title_surf = font_title.render("GOMOKU", True, (40, 40, 40))
        self.title_rect = self.title_surf.get_rect(center=(SCREEN_WIDTH // 2, 150))

        center_x = SCREEN_WIDTH // 2
        
        # [NEW] Mode Toggle Button
        self.btn_mode = Button(center_x, 280, 240, 50, f"Rule: {self.current_rule}-in-a-Row", font_button, MODE_COLOR, MODE_HOVER)
        
        self.btn_ai = Button(center_x, 350, 240, 60, "Player vs AI", font_button, BUTTON_COLOR, BUTTON_HOVER)
        self.btn_pvp = Button(center_x, 430, 240, 60, "Player vs Player", font_button, BUTTON_COLOR, BUTTON_HOVER)
        self.btn_quit = Button(center_x, 510, 240, 60, "Quit Game", font_button, QUIT_COLOR, QUIT_HOVER)

    def run(self):
        """ Returns: (action, rule_length) e.g., ('ai', 6) """
        clock = pygame.time.Clock()
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == QUIT: return None, 5
                
                # [NEW] Handle Mode Toggle
                if self.btn_mode.is_clicked(event):
                    # Toggle between 5 and 6
                    if self.current_rule == 5: self.current_rule = 6
                    else: self.current_rule = 5
                    # Update Text
                    self.btn_mode.text = f"Rule: {self.current_rule}-in-a-Row"
                
                # Handle Game Start
                if self.btn_ai.is_clicked(event): return 'ai', self.current_rule
                if self.btn_pvp.is_clicked(event): return 'pvp', self.current_rule
                if self.btn_quit.is_clicked(event): return None, 5

            # Updates
            self.btn_mode.check_hover(mouse_pos)
            self.btn_ai.check_hover(mouse_pos)
            self.btn_pvp.check_hover(mouse_pos)
            self.btn_quit.check_hover(mouse_pos)

            # Drawing
            self.screen.blit(self.background_img, (0, 0))
            self.screen.blit(self.title_surf, self.title_rect)
            
            self.btn_mode.draw(self.screen) # Draw Mode Button
            self.btn_ai.draw(self.screen)
            self.btn_pvp.draw(self.screen)
            self.btn_quit.draw(self.screen)

            pygame.display.update()
            clock.tick(30)