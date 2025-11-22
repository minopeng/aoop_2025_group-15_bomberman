# game_board.py
from constants import LEVEL

class GameBoard:
    """Manages board state, victory conditions, and move history."""
    def __init__(self):
        self.level = LEVEL
        # 0:Empty, 1:Black, -1:White
        self.grid = [[0 for _ in range(self.level)] for _ in range(self.level)]
        self.move_count = 0
        self.history = []  # [NEW] Store moves as (x, y) tuples

    def place_stone(self, x, y, color):
        """Places a stone at (x, y)"""
        if self.is_valid(x, y) and self.is_empty(x, y):
            self.grid[x][y] = color
            self.move_count += 1
            self.history.append((x, y)) # [NEW] Record the move
            return True
        return False

    def undo_last_move(self): # [NEW] Function to undo
        """Removes the last stone placed."""
        if not self.history:
            return False # No moves to undo
            
        last_x, last_y = self.history.pop()
        self.grid[last_x][last_y] = 0
        self.move_count -= 1
        return True

    def is_empty(self, x, y):
        return self.grid[x][y] == 0

    def is_valid(self, x, y):
        return 0 <= x < self.level and 0 <= y < self.level

    def is_full(self):
        return self.move_count == self.level * self.level

    def check_win(self, x, y, color, length=4):
        # (Keep your existing check_win code exactly as it is)
        count1, count2, count3, count4 = 0, 0, 0, 0
        
        # Horizontal
        i = x - 1
        while (i >= 0):
            if color == self.grid[i][y]:
                count1 += 1
                i -= 1
            else: break
        i = x + 1
        while i < self.level:
            if self.grid[i][y] == color:
                count1 += 1
                i += 1
            else: break

        # Vertical
        j = y - 1
        while (j >= 0):
            if self.grid[x][j] == color:
                count2 += 1
                j -= 1
            else: break
        j = y + 1
        while j < self.level:
            if self.grid[x][j] == color:
                count2 += 1
                j += 1
            else: break

        # Diagonal
        i, j = x - 1, y - 1
        while (i >= 0 and j >= 0):
            if self.grid[i][j] == color:
                count3 += 1
                i -= 1
                j -= 1
            else: break
        i, j = x + 1, y + 1
        while (i < self.level and j < self.level):
            if self.grid[i][j] == color:
                count3 += 1
                i += 1
                j += 1
            else: break
        
        # Anti-Diagonal
        i, j = x + 1, y - 1
        while (i < self.level and j >= 0):
            if self.grid[i][j] == color:
                count4 += 1
                i += 1
                j -= 1
            else: break
        i, j = x - 1, y + 1
        while (i >= 0 and j < self.level):
            if self.grid[i][j] == color:
                count4 += 1
                i -= 1
                j += 1
            else: break

        if count1 >= length or count2 >= length or count3 >= length or count4 >= length:
            return True
        else:
            return False