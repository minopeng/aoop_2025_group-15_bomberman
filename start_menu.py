# start_menu.py
# 包含 StartMenu 類別

import pygame
from pygame.locals import *
from constants import SCREEN_WIDTH

class StartMenu:
    """處理初始選單的顯示和邏輯"""
    def __init__(self, screen, background_img, font_title, font_button):
        self.screen = screen
        self.background_img = background_img
        self.font_title = font_title
        self.font_button = font_button
        
        # 按鈕顏色
        self.btn_color = (60, 179, 113)
        self.btn_hover_color = (46, 139, 87)
        self.text_color = (255, 255, 255)
        
        # 標題
        self.title_text = self.font_title.render('五子棋對戰', True, (30, 30, 30))
        self.title_rect = self.title_text.get_rect(center=(SCREEN_WIDTH // 2, 250))
        
        # 按鈕 1: AI
        self.btn_ai_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 350, 200, 60)
        self.btn_ai_text = self.font_button.render('AI 對戰', True, self.text_color)
        self.btn_ai_text_rect = self.btn_ai_text.get_rect(center=self.btn_ai_rect.center)
        
        # 按鈕 2: PvP
        self.btn_pvp_rect = pygame.Rect(SCREEN_WIDTH // 2 - 100, 450, 200, 60)
        self.btn_pvp_text = self.font_button.render('玩家對戰', True, self.text_color)
        self.btn_pvp_text_rect = self.btn_pvp_text.get_rect(center=self.btn_pvp_rect.center)

    def run(self):
        """
        執行選單迴圈，返回 'ai', 'pvp' 或 None (退出)
        """
        while True:
            mouse_pos = pygame.mouse.get_pos()
            
            for event in pygame.event.get():
                if event.type == QUIT:
                    return None # 表示退出
                if event.type == MOUSEBUTTONDOWN:
                    if self.btn_ai_rect.collidepoint(mouse_pos):
                        return 'ai' # 選擇 AI
                    if self.btn_pvp_rect.collidepoint(mouse_pos):
                        return 'pvp' # 選擇 PvP
            
            self._draw(mouse_pos)

    def _draw(self, mouse_pos):
        """繪製選單"""
        self.screen.blit(self.background_img, (0, 0))
        self.screen.blit(self.title_text, self.title_rect)
        
        # 繪製 AI 按鈕
        if self.btn_ai_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, self.btn_hover_color, self.btn_ai_rect, border_radius=15)
        else:
            pygame.draw.rect(self.screen, self.btn_color, self.btn_ai_rect, border_radius=15)
        self.screen.blit(self.btn_ai_text, self.btn_ai_text_rect)
        
        # 繪製 PvP 按鈕
        if self.btn_pvp_rect.collidepoint(mouse_pos):
            pygame.draw.rect(self.screen, self.btn_hover_color, self.btn_pvp_rect, border_radius=15)
        else:
            pygame.draw.rect(self.screen, self.btn_color, self.btn_pvp_rect, border_radius=15)
        self.screen.blit(self.btn_pvp_text, self.btn_pvp_text_rect)
        
        pygame.display.update()