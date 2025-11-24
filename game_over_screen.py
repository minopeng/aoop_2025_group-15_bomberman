# game_board.py
from constants import LEVEL

class GameBoard:
    def __init__(self, target_length=5): # [NEW] Accept target length
        self.level = LEVEL
        self.grid = [[0 for _ in range(self.level)] for _ in range(self.level)]
        self.move_count = 0
        self.history = []
        self.target_length = target_length # [NEW] Store it

    # ... (place_stone, undo_last_move, is_empty, is_valid, is_full remain the same) ...

    def check_win(self, x, y, color):
        # Use self.target_length instead of hardcoded 4 or 5
        length = self.target_length 
        
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

        # Check against target_length - 1 (because count excludes the current stone)
        # OR simply: if count + 1 >= self.target_length
        # Your original code counted neighbors. So if neighbors >= length-1, it's a win.
        target_neighbors = self.target_length - 1
        
        if count1 >= target_neighbors or count2 >= target_neighbors or \
           count3 >= target_neighbors or count4 >= target_neighbors:
            return True
        else:
            return False