import pygame
from pygame.locals import *
from constants import SCREEN_WIDTH
from ui import Button

class StartMenu:
    def __init__(self, screen, background_img, font_title, font_button):
        self.screen = screen
        self.background_img = background_img
        self.font_button = font_button
        
        # 遊戲設定狀態
        self.current_rule = 5 
        self.themes = ['Classic', 'Dark', 'Paper'] # [新增] 主題列表
        self.theme_index = 0
        
        # Colors
        BUTTON_COLOR = (70, 130, 180)
        BUTTON_HOVER = (100, 149, 237)
        MODE_COLOR   = (46, 139, 87)  
        MODE_HOVER   = (60, 179, 113)
        THEME_COLOR  = (147, 112, 219) # [新增] 紫色按鈕給主題
        THEME_HOVER  = (186, 85, 211)
        QUIT_COLOR   = (205, 92, 92)
        QUIT_HOVER   = (255, 99, 71)
        
        self.title_surf = font_title.render("Board Game Arena", True, (40, 40, 40))
        self.title_rect = self.title_surf.get_rect(center=(SCREEN_WIDTH // 2, 130)) # 標題往上移一點

        center_x = SCREEN_WIDTH // 2
        
        # Buttons (調整 Y 軸位置，塞入新按鈕)
        self.btn_theme = Button(center_x, 230, 240, 50, self._get_theme_text(), font_button, THEME_COLOR, THEME_HOVER)
        self.btn_mode  = Button(center_x, 300, 240, 50, self._get_rule_text(), font_button, MODE_COLOR, MODE_HOVER)
        self.btn_ai    = Button(center_x, 370, 240, 60, "Player vs AI", font_button, BUTTON_COLOR, BUTTON_HOVER)
        self.btn_pvp   = Button(center_x, 450, 240, 60, "Player vs Player", font_button, BUTTON_COLOR, BUTTON_HOVER)
        self.btn_quit  = Button(center_x, 530, 240, 60, "Quit Game", font_button, QUIT_COLOR, QUIT_HOVER)

    def _get_rule_text(self):
        if self.current_rule == 'go': return "Mode: Go (Weiqi)"
        else: return f"Rule: {self.current_rule}-in-a-Row"

    def _get_theme_text(self):
        return f"Theme: {self.themes[self.theme_index]}"

    def run(self):
        """ Returns: (action, rule_length, theme_name) """
        clock = pygame.time.Clock()
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == QUIT: return None, 5, 'Classic'
                if event.type == KEYDOWN and event.key == K_q: return None, 5, 'Classic'
                
                # [新增] 切換主題
                if self.btn_theme.is_clicked(event):
                    self.theme_index = (self.theme_index + 1) % len(self.themes)
                    self.btn_theme.text = self._get_theme_text()

                # 切換規則
                if self.btn_mode.is_clicked(event):
                    if self.current_rule == 5: self.current_rule = 6
                    elif self.current_rule == 6: self.current_rule = 4
                    elif self.current_rule == 4: self.current_rule = 'go'
                    else: self.current_rule = 5
                    self.btn_mode.text = self._get_rule_text()
                
                # 開始遊戲 (現在多回傳一個 theme)
                current_theme = self.themes[self.theme_index]
                
                if self.btn_ai.is_clicked(event): 
                    if self.current_rule == 'go':
                        print("AI not available for Go mode yet. Switching to PvP.")
                        return 'pvp', 'go', current_theme
                    return 'ai', self.current_rule, current_theme
                    
                if self.btn_pvp.is_clicked(event): 
                    return 'pvp', self.current_rule, current_theme
                    
                if self.btn_quit.is_clicked(event): return None, 5, 'Classic'

            # Draw
            self.btn_theme.check_hover(mouse_pos)
            self.btn_mode.check_hover(mouse_pos)
            self.btn_ai.check_hover(mouse_pos)
            self.btn_pvp.check_hover(mouse_pos)
            self.btn_quit.check_hover(mouse_pos)

            self.screen.blit(self.background_img, (0, 0))
            self.screen.blit(self.title_surf, self.title_rect)
            
            self.btn_theme.draw(self.screen) # 畫出主題按鈕
            self.btn_mode.draw(self.screen)
            self.btn_ai.draw(self.screen)
            self.btn_pvp.draw(self.screen)
            self.btn_quit.draw(self.screen)

            pygame.display.update()
            clock.tick(30)