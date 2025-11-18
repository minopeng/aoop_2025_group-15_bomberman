# game_board.py
# 包含 GameBoard 類別

from constants import LEVEL

class GameBoard:
    """管理棋盤狀態和勝利條件"""
    def __init__(self):
        self.level = LEVEL # 使用常數
        # 使用 0:空, 1:黑棋, -1:白棋
        self.grid = [[0 for _ in range(self.level)] for _ in range(self.level)]
        self.move_count = 0 # 用於判斷平局

    def place_stone(self, x, y, color):
        """在 (x, y) 位置落子"""
        if self.is_valid(x, y) and self.is_empty(x, y):
            self.grid[x][y] = color
            self.move_count += 1
            return True
        return False

    def is_empty(self, x, y):
        """檢查 (x, y) 是否為空"""
        return self.grid[x][y] == 0

    def is_valid(self, x, y):
        """檢查 (x, y) 是否在棋盤內"""
        return 0 <= x < self.level and 0 <= y < self.level

    def is_full(self):
        """檢查棋盤是否已滿 (平局)"""
        return self.move_count == self.level * self.level

    def check_win(self, x, y, color, length=4):
        """
        檢查剛下的這步棋 (x, y, color) 是否導致勝利
        (原來的 Judge 函式)
        """
        count1, count2, count3, count4 = 0, 0, 0, 0
        # 横向判断
        i = x - 1
        while (i >= 0):
            if color == self.grid[i][y]:
                count1 += 1
                i -= 1
            else:
                break
        i = x + 1
        while i < self.level:
            if self.grid[i][y] == color:
                count1 += 1
                i += 1
            else:
                break

        # 纵向判断
        j = y - 1
        while (j >= 0):
            if self.grid[x][j] == color:
                count2 += 1
                j -= 1
            else:
                break
        j = y + 1
        while j < self.level:
            if self.grid[x][j] == color:
                count2 += 1
                j += 1
            else:
                break

        # 正对角线判断
        i, j = x - 1, y - 1
        while (i >= 0 and j >= 0):
            if self.grid[i][j] == color:
                count3 += 1
                i -= 1
                j -= 1
            else:
                break
        i, j = x + 1, y + 1
        while (i < self.level and j < self.level):
            if self.grid[i][j] == color:
                count3 += 1
                i += 1
                j += 1
            else:
                break
        
        # 反对角线判断
        i, j = x + 1, y - 1
        while (i < self.level and j >= 0):
            if self.grid[i][j] == color:
                count4 += 1
                i += 1
                j -= 1
            else:
                break
        i, j = x - 1, y + 1
        while (i >= 0 and j < self.level):
            if self.grid[i][j] == color:
                count4 += 1
                i -= 1
                j += 1
            else:
                break

        if count1 >= length or count2 >= length or count3 >= length or count4 >= length:
            return True
        else:
            return False