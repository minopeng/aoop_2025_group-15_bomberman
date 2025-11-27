import pygame
from pygame.locals import *
from constants import SCREEN_WIDTH
from ui import Button, Slider

class StartMenu:
    def __init__(self, screen, background_img, font_title, font_button):
        self.screen = screen
        self.background_img = background_img
        self.font_button = font_button
        self.font_title = font_title
        
        # State
        self.state = "main" # 'main' or 'settings'
        
        # Settings Data
        self.current_rule = 5 
        self.themes = ['Classic', 'Dark', 'Paper', 'Ocean', 'Matrix', 'Pink'] 
        self.theme_index = 0
        self.volume = 0.8 # Default volume
        
        # --- UI Elements Setup ---
        self._init_main_menu()
        self._init_settings_menu()

    def _init_main_menu(self):
        cx = SCREEN_WIDTH // 2
        # Main Menu Buttons
        self.btn_local = Button(cx, 280, 260, 50, "Local Game (PvP / AI)", self.font_button, (70, 130, 180), (100, 149, 237))
        self.btn_lan   = Button(cx, 350, 260, 50, "LAN Battle (Online)", self.font_button, (255, 140, 0), (255, 165, 0))
        self.btn_set   = Button(cx, 420, 260, 50, "Settings & Rules", self.font_button, (100, 100, 100), (120, 120, 120))
        self.btn_quit  = Button(cx, 490, 260, 50, "Quit Game (Q)", self.font_button, (205, 92, 92), (255, 99, 71))
        
        # Sub-buttons for LAN
        self.btn_host = Button(cx, 280, 260, 50, "Create Room (Host)", self.font_button, (46, 139, 87), (60, 179, 113))
        self.btn_join = Button(cx, 350, 260, 50, "Join Room (Client)", self.font_button, (46, 139, 87), (60, 179, 113))
        self.btn_back_lan = Button(cx, 420, 260, 50, "Back (R)", self.font_button, (100, 100, 100), (120, 120, 120))
        self.show_lan_options = False

        # Sub-buttons for Local
        self.btn_pva = Button(cx, 280, 260, 50, "Player vs AI", self.font_button, (70, 130, 180), (100, 149, 237))
        self.btn_pvp = Button(cx, 350, 260, 50, "Player vs Player", self.font_button, (70, 130, 180), (100, 149, 237))
        self.btn_back_loc = Button(cx, 420, 260, 50, "Back (R)", self.font_button, (100, 100, 100), (120, 120, 120))
        self.show_local_options = False

    def _init_settings_menu(self):
        cx = SCREEN_WIDTH // 2
        # Settings Buttons
        self.btn_rule = Button(cx, 250, 300, 50, self._get_rule_text(), self.font_button, (46, 139, 87), (60, 179, 113))
        self.btn_theme = Button(cx, 320, 300, 50, self._get_theme_text(), self.font_button, (147, 112, 219), (186, 85, 211))
        
        # Volume Slider
        self.slider_vol = Slider(cx - 20, 400, 200, 10, 0.0, 1.0, self.volume)
        
        self.btn_back_set = Button(cx, 500, 200, 50, "Back to Main (R)", self.font_button, (100, 100, 100), (120, 120, 120))

    def _get_rule_text(self):
        if self.current_rule == 'go': return "Mode: Go (Weiqi)"
        return f"Rule: {self.current_rule}-in-a-Row"

    def _get_theme_text(self):
        return f"Theme: {self.themes[self.theme_index]}"

    def run(self):
        clock = pygame.time.Clock()
        
        while True:
            mouse_pos = pygame.mouse.get_pos()
            events = pygame.event.get()
            
            for event in events:
                if event.type == QUIT: 
                    return None, 5, 'Classic', 0.8
                
                # --- [關鍵修改] 鍵盤快捷鍵處理 ---
                if event.type == KEYDOWN:
                    # 1. 全域退出 (按 Q)
                    if event.key == K_q:
                        return None, 5, 'Classic', 0.8
                    
                    # 2. 返回上一頁 (按 R)
                    if event.key == K_r:
                        if self.state == "settings":
                            self.state = "main"
                        # [新增] 如果正在顯示子選單，按 R 就關閉子選單回到主選單
                        elif self.show_lan_options:
                            self.show_lan_options = False
                        elif self.show_local_options:
                            self.show_local_options = False
                # ---------------------------

                if self.state == "settings":
                    self.volume = self.slider_vol.handle_event(event)

            self.screen.blit(self.background_img, (0, 0))
            
            # Draw Title
            title_text = "Board Game Arena" if self.state == "main" else "Settings"
            title_surf = self.font_title.render(title_text, True, (40, 40, 40))
            self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100)))

            if self.state == "main":
                if self.show_lan_options:
                    # LAN Sub-menu
                    self._draw_buttons([self.btn_host, self.btn_join, self.btn_back_lan], mouse_pos, events)
                    if self._check_click(self.btn_host, events): return 'lan_host', self.current_rule, self.themes[self.theme_index], self.volume
                    if self._check_click(self.btn_join, events): return 'lan_join', self.current_rule, self.themes[self.theme_index], self.volume
                    if self._check_click(self.btn_back_lan, events): self.show_lan_options = False
                
                elif self.show_local_options:
                    # Local Sub-menu
                    self._draw_buttons([self.btn_pva, self.btn_pvp, self.btn_back_loc], mouse_pos, events)
                    if self._check_click(self.btn_pva, events): 
                        if self.current_rule == 'go': return 'pvp', 'go', self.themes[self.theme_index], self.volume
                        return 'ai', self.current_rule, self.themes[self.theme_index], self.volume
                    if self._check_click(self.btn_pvp, events): return 'pvp', self.current_rule, self.themes[self.theme_index], self.volume
                    if self._check_click(self.btn_back_loc, events): self.show_local_options = False

                else:
                    # Root menu
                    self._draw_buttons([self.btn_local, self.btn_lan, self.btn_set, self.btn_quit], mouse_pos, events)
                    
                    if self._check_click(self.btn_local, events): self.show_local_options = True
                    if self._check_click(self.btn_lan, events): self.show_lan_options = True
                    if self._check_click(self.btn_set, events): self.state = "settings"
                    if self._check_click(self.btn_quit, events): return None, 5, 'Classic', 0.8

            elif self.state == "settings":
                self._draw_buttons([self.btn_rule, self.btn_theme, self.btn_back_set], mouse_pos, events)
                
                vol_label = self.font_button.render("Volume:", True, (50, 50, 50))
                self.screen.blit(vol_label, (self.slider_vol.rect.left - 100, self.slider_vol.rect.top - 5))
                self.slider_vol.draw(self.screen, self.font_button)

                if self._check_click(self.btn_rule, events):
                    if self.current_rule == 5: self.current_rule = 6
                    elif self.current_rule == 6: self.current_rule = 4
                    elif self.current_rule == 4: self.current_rule = 'go'
                    else: self.current_rule = 5
                    self.btn_rule.text = self._get_rule_text()
                
                if self._check_click(self.btn_theme, events):
                    self.theme_index = (self.theme_index + 1) % len(self.themes)
                    self.btn_theme.text = self._get_theme_text()
                    
                if self._check_click(self.btn_back_set, events): self.state = "main"

            pygame.display.update()
            clock.tick(30)

    def _draw_buttons(self, buttons, mouse_pos, events):
        for btn in buttons:
            btn.check_hover(mouse_pos)
            btn.draw(self.screen)

    def _check_click(self, btn, events):
        for e in events:
            if btn.is_clicked(e): return True
        return False