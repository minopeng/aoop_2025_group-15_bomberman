import pygame

class Button:
    """A modern button with hover effects and rounded corners."""
    def __init__(self, center_x, center_y, width, height, text, font, base_color, hover_color, text_color=(255,255,255)):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (center_x, center_y)
        self.text = text
        self.font = font
        self.base_color = base_color
        self.hover_color = hover_color
        self.text_color = text_color
        self.is_hovered = False

    def check_hover(self, mouse_pos):
        """Updates hover state based on mouse position."""
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, event):
        """Checks if the button was left-clicked."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

    def draw(self, screen):
        """Draws the button with the appropriate color."""
        color = self.hover_color if self.is_hovered else self.base_color
        
        # Draw button body with rounded corners
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        
        # Draw text centered
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)