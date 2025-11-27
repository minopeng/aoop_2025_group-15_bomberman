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
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        return self.is_hovered

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_hovered:
                return True
        return False

    def draw(self, screen):
        color = self.hover_color if self.is_hovered else self.base_color
        pygame.draw.rect(screen, color, self.rect, border_radius=12)
        text_surf = self.font.render(self.text, True, self.text_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

class Slider:
    """A simple slider for volume control."""
    def __init__(self, center_x, center_y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(0, 0, width, height)
        self.rect.center = (center_x, center_y)
        self.min_val = min_val
        self.max_val = max_val
        self.current_val = initial_val
        self.dragging = False
        
        # Handle (The circle you drag)
        self.handle_radius = height + 4
        self.handle_rect = pygame.Rect(0, 0, self.handle_radius*2, self.handle_radius*2)
        self.update_handle_pos()

    def update_handle_pos(self):
        # Map value to pixel position
        ratio = (self.current_val - self.min_val) / (self.max_val - self.min_val)
        handle_x = self.rect.left + (self.rect.width * ratio)
        self.handle_rect.center = (int(handle_x), self.rect.centery)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.handle_rect.collidepoint(event.pos) or self.rect.collidepoint(event.pos):
                self.dragging = True
                self.update_val_from_pos(event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.dragging:
                self.update_val_from_pos(event.pos[0])
                
        return self.current_val

    def update_val_from_pos(self, mouse_x):
        # Map pixel position back to value
        if mouse_x < self.rect.left: mouse_x = self.rect.left
        if mouse_x > self.rect.right: mouse_x = self.rect.right
        
        ratio = (mouse_x - self.rect.left) / self.rect.width
        self.current_val = self.min_val + (self.max_val - self.min_val) * ratio
        self.update_handle_pos()

    def draw(self, screen, font):
        # Draw Bar
        pygame.draw.rect(screen, (200, 200, 200), self.rect, border_radius=5)
        # Draw Filled part
        filled_rect = pygame.Rect(self.rect.left, self.rect.top, self.handle_rect.centerx - self.rect.left, self.rect.height)
        pygame.draw.rect(screen, (100, 200, 100), filled_rect, border_radius=5)
        # Draw Handle
        pygame.draw.circle(screen, (255, 255, 255), self.handle_rect.center, self.handle_radius)
        # Draw Text Value
        val_surf = font.render(f"{int(self.current_val*100)}%", True, (255, 255, 255))
        screen.blit(val_surf, (self.rect.right + 15, self.rect.top - 5))