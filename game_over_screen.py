import pygame
from pygame.locals import *
from constants import SCREEN_WIDTH, SCREEN_HEIGHT
from ui import Button

class GameOverScreen:
    def __init__(self, screen, font_title, font_button):
        self.screen = screen
        self.font_title = font_title
        self.font_button = font_button
        
        # Create a semi-transparent overlay surface (Black with ~70% opacity)
        self.overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        self.overlay.fill((0, 0, 0, 180))

        # Buttons (English Text)
        center_x = SCREEN_WIDTH // 2
        self.btn_restart = Button(center_x, 400, 220, 50, "Play Again", font_button, (60, 179, 113), (46, 139, 87))
        self.btn_menu = Button(center_x, 470, 220, 50, "Main Menu", font_button, (70, 130, 180), (100, 149, 237))
        self.btn_quit = Button(center_x, 540, 220, 50, "Quit", font_button, (205, 92, 92), (255, 99, 71))

    def run(self, winner_color):
        """
        Displays the Game Over screen over the existing board.
        Returns: 'restart', 'menu', or None (quit)
        """
        # Take a snapshot of the current game board (background)
        background_snap = self.screen.copy()
        
        # Prepare Winner Text
        if winner_color == 1:
            text = "Black Wins!"
            color = (100, 255, 100) # Greenish
        elif winner_color == -1:
            text = "White Wins!"
            color = (255, 100, 100) # Reddish
        else:
            text = "Draw!"
            color = (200, 200, 200)

        title_surf = self.font_title.render(text, True, color)
        title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 250))
        
        clock = pygame.time.Clock()
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    return None
                
                if self.btn_restart.is_clicked(event): return 'restart'
                if self.btn_menu.is_clicked(event): return 'menu'
                if self.btn_quit.is_clicked(event): return None

            # Update Button Hovers
            self.btn_restart.check_hover(mouse_pos)
            self.btn_menu.check_hover(mouse_pos)
            self.btn_quit.check_hover(mouse_pos)

            # Draw
            self.screen.blit(background_snap, (0, 0)) # Draw the frozen game board
            self.screen.blit(self.overlay, (0, 0))    # Draw dark overlay
            
            self.screen.blit(title_surf, title_rect)
            
            self.btn_restart.draw(self.screen)
            self.btn_menu.draw(self.screen)
            self.btn_quit.draw(self.screen)
            
            pygame.display.update()
            clock.tick(30)