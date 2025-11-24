# game_board.py
from constants import LEVEL

class GameBoard:
    """Manages board state, victory conditions, and move history."""
    def __init__(self, target_length=5): # [CHANGED] Accept rule setting
        self.level = LEVEL
        self.target_length = target_length 
        self.grid = [[0 for _ in range(self.level)] for _ in range(self.level)]
        self.move_count = 0
        self.history = []

    def place_stone(self, x, y, color):
        if self.is_valid(x, y) and self.is_empty(x, y):
            self.grid[x][y] = color
            self.move_count += 1
            self.history.append((x, y))
            return True
        return False

    def undo_last_move(self):
        if not self.history: return False
        last_x, last_y = self.history.pop()
        self.grid[last_x][last_y] = 0
        self.move_count -= 1
        return True

    def is_empty(self, x, y): return self.grid[x][y] == 0
    def is_valid(self, x, y): return 0 <= x < self.level and 0 <= y < self.level
    def is_full(self): return self.move_count == self.level * self.level

    def check_win(self, x, y, color):
        # [CHANGED] Dynamically check based on target_length
        required = self.target_length - 1
        count1, count2, count3, count4 = 0, 0, 0, 0
        
        # Horizontal
        i = x - 1
        while i >= 0 and self.grid[i][y] == color:
            count1 += 1; i -= 1
        i = x + 1
        while i < self.level and self.grid[i][y] == color:
            count1 += 1; i += 1

        # Vertical
        j = y - 1
        while j >= 0 and self.grid[x][j] == color:
            count2 += 1; j -= 1
        j = y + 1
        while j < self.level and self.grid[x][j] == color:
            count2 += 1; j += 1

        # Diagonal
        i, j = x - 1, y - 1
        while i >= 0 and j >= 0 and self.grid[i][j] == color:
            count3 += 1; i -= 1; j -= 1
        i, j = x + 1, y + 1
        while i < self.level and j < self.level and self.grid[i][j] == color:
            count3 += 1; i += 1; j += 1
        
        # Anti-Diagonal
        i, j = x + 1, y - 1
        while i < self.level and j >= 0 and self.grid[i][j] == color:
            count4 += 1; i += 1; j -= 1
        i, j = x - 1, y + 1
        while i >= 0 and j < self.level and self.grid[i][j] == color:
            count4 += 1; i -= 1; j += 1

        if count1 >= required or count2 >= required or count3 >= required or count4 >= required:
            return True
        return False