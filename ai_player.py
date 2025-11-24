# ai_player.py
from random import randint
from constants import LEVEL, GRADE, MAX_SCORE

class AIPlayer:
    def __init__(self, target_length=5):
        self.level = LEVEL
        self.grade = GRADE
        self.MAX_SCORE = MAX_SCORE
        self.ai_move_count = 0
        self.target_length = target_length

    def get_move(self, board_grid, last_move_x, last_move_y, ai_color):
        self.ai_move_count += 1
        # Optimization: Early game random start
        if self.ai_move_count < 2:
            return self._autoplay(board_grid, last_move_x, last_move_y)
        
        shape_Player = self._scan(board_grid, -ai_color)
        shape_AI = self._scan(board_grid, ai_color)

        shape_Player = self._sort(shape_Player)
        shape_AI = self._sort(shape_AI)

        max_x_P, max_y_P, max_P = self._evaluate(shape_Player)
        max_x_AI, max_y_AI, max_AI = self._evaluate(shape_AI)

        if max_P > max_AI and max_AI < self.MAX_SCORE:
            return max_x_P, max_y_P
        else:
            return max_x_AI, max_y_AI

    def _scan(self, chesspad, color):
        """
        Scans board. 
        - Restores scoring for counts 1, 2, 3 (Previous functions).
        - Applies strict space limitation ONLY for count 4 (5-in-a-row).
        """
        shape = [[[0 for _ in range(5)] for _ in range(self.level)] for _ in range(self.level)]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for i in range(self.level):
            for j in range(self.level):
                if chesspad[i][j] != 0: continue

                for d_idx, (dr, dc) in enumerate(directions):
                    # 1. Count Neighbors
                    count = 0
                    
                    # Forward
                    r, c = i + dr, j + dc
                    while 0 <= r < self.level and 0 <= c < self.level and chesspad[r][c] == color:
                        count += 1
                        r += dr
                        c += dc
                    end_r1, end_c1 = r, c
                        
                    # Backward
                    r, c = i - dr, j - dc
                    while 0 <= r < self.level and 0 <= c < self.level and chesspad[r][c] == color:
                        count += 1
                        r -= dr
                        c -= dc
                    end_r2, end_c2 = r, c

                    # 2. Calculate Space (Potential)
                    current_len = count + 1
                    spaces_found = 0
                    
                    r, c = end_r1, end_c1
                    while 0 <= r < self.level and 0 <= c < self.level and chesspad[r][c] == 0:
                        spaces_found += 1
                        r += dr
                        c += dc
                        
                    r, c = end_r2, end_c2
                    while 0 <= r < self.level and 0 <= c < self.level and chesspad[r][c] == 0:
                        spaces_found += 1
                        r -= dr
                        c -= dc
                    
                    total_potential = current_len + spaces_found

                    # 3. Apply Scoring
                    
                    # [Case A] Instant Win (6 stones / 5 neighbors)
                    if count >= 5:
                        shape[i][j][d_idx] += (self.grade * 5) + 10000 

                    # [Case B] 5 stones (4 neighbors) - THE STRICT LIMITATION
                    elif count == 4:
                        if total_potential >= 6:
                            shape[i][j][d_idx] += (self.grade * 4) + spaces_found
                        else:
                            shape[i][j][d_idx] += 0 # Dead line, no score

                    # [Case C] Previous Functions Restored (1, 2, 3 neighbors)
                    # We give them standard points so the AI builds up attacks.
                    elif count == 3:
                        shape[i][j][d_idx] += (self.grade * 3) + spaces_found
                    elif count == 2:
                        shape[i][j][d_idx] += (self.grade * 2) + spaces_found
                    elif count == 1:
                        shape[i][j][d_idx] += (self.grade * 1) + spaces_found

        return shape

    def _sort(self, shape):
        for i in range(self.level):
            for j in range(self.level):
                cell = shape[i][j]
                for x in range(4):
                    for w in range(3, x, -1):
                        if cell[w - 1] < cell[w]:
                            temp = cell[w]
                            cell[w] = cell[w - 1]
                            cell[w - 1] = temp
        return shape

    def _evaluate(self, shape):
        winning_score = 5000 
        
        for i in range(self.level):
            for j in range(self.level):
                if (shape[i][j][0] >= winning_score or 
                    shape[i][j][1] >= winning_score or 
                    shape[i][j][2] >= winning_score or 
                    shape[i][j][3] >= winning_score):
                    return i, j, self.MAX_SCORE
                
                shape[i][j][4] = (shape[i][j][0] * 1000 + 
                                  shape[i][j][1] * 100 + 
                                  shape[i][j][2] * 10 + 
                                  shape[i][j][3])

        max_x, max_y, max_val = 0, 0, 0
        for i in range(self.level):
            for j in range(self.level):
                if max_val < shape[i][j][4]:
                    max_val = shape[i][j][4]
                    max_x = i
                    max_y = j
        return max_x, max_y, max_val

    def _autoplay(self, ch, m, n):
        a1 = [1, -1, 1, -1, 1, -1, 0, 0]
        b1 = [1, -1, -1, 1, 0, 0, 1, -1]
        rand = randint(0, 7)
        tries = 0
        while tries < 20:
            tx = m + a1[rand]
            ty = n + b1[rand]
            if 0 <= tx < self.level and 0 <= ty < self.level and ch[tx][ty] == 0:
                return tx, ty
            rand = randint(0, 7)
            tries += 1
        return self._find_random_empty(ch)

    def _find_random_empty(self, ch):
        empty_spots = []
        for i in range(self.level):
            for j in range(self.level):
                if ch[i][j] == 0:
                    empty_spots.append((i,j))
        if not empty_spots: return -1, -1
        return empty_spots[randint(0, len(empty_spots) - 1)]