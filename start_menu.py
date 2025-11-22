import pygame
from pygame.locals import *
from constants import SCREEN_WIDTH
from ui import Button

class StartMenu:
    """Start Menu with AI, PvP, and Quit options."""
    def __init__(self, screen, background_img, font_title, font_button):
        self.screen = screen
        self.background_img = background_img
        
        # Theme Colors
        BUTTON_COLOR = (70, 130, 180)       # Steel Blue
        BUTTON_HOVER = (100, 149, 237)      # Cornflower Blue
        QUIT_COLOR = (205, 92, 92)          # Indian Red
        QUIT_HOVER = (255, 99, 71)          # Tomato
        
        # Title: Render "GOMOKU"
        self.title_surf = font_title.render("GOMOKU", True, (40, 40, 40))
        self.title_rect = self.title_surf.get_rect(center=(SCREEN_WIDTH // 2, 200))

        # Create Buttons (English Text)
        center_x = SCREEN_WIDTH // 2
        self.btn_ai = Button(center_x, 350, 240, 60, "Player vs AI", font_button, BUTTON_COLOR, BUTTON_HOVER)
        self.btn_pvp = Button(center_x, 430, 240, 60, "Player vs Player", font_button, BUTTON_COLOR, BUTTON_HOVER)
        self.btn_quit = Button(center_x, 510, 240, 60, "Quit Game", font_button, QUIT_COLOR, QUIT_HOVER)

    def run(self):
        """
        Displays the menu loop. 
        Returns: 'ai', 'pvp', or None (if quitting).
        """
        clock = pygame.time.Clock()
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    return None
                
                # Check clicks
                if self.btn_ai.is_clicked(event): return 'ai'
                if self.btn_pvp.is_clicked(event): return 'pvp'
                if self.btn_quit.is_clicked(event): return None

            # Update Hover States
            self.btn_ai.check_hover(mouse_pos)
            self.btn_pvp.check_hover(mouse_pos)
            self.btn_quit.check_hover(mouse_pos)

            # Drawing
            self.screen.blit(self.background_img, (0, 0))
            
            # Draw Title Shadow then Title
            shadow_surf = self.title_surf.copy()
            shadow_surf.fill((200, 200, 200), special_flags=pygame.BLEND_RGBA_MULT)
            self.screen.blit(shadow_surf, (self.title_rect.x + 3, self.title_rect.y + 3))
            self.screen.blit(self.title_surf, self.title_rect)
            
            # Draw Buttons
            self.btn_ai.draw(self.screen)
            self.btn_pvp.draw(self.screen)
            self.btn_quit.draw(self.screen)

            pygame.display.update()
            clock.tick(30)