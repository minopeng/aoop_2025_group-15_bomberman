import random
from random import randint

# --- CONFIGURATION ---
# These constants define "How scared" the AI is of certain shapes.
SCORE_WIN = 100000       # 4-in-a-row (Immediate Win)
SCORE_LIVE_3 = 10000     # _XXX_ (Unstoppable win next turn)
SCORE_DEAD_3 = 1000      # _XXX or XXX_ (Must block)
SCORE_LIVE_2 = 1000      # _XX_ (Good potential)
SCORE_DEAD_2 = 100       # _XX or XX_ (Weak)

class TeacherAI_4Row:
    """
    Advanced Heuristic AI for 4-in-a-row.
    Adapted from the robust logic of ai_player.py
    """
    def __init__(self, target_length=4):
        self.level = 15      # Board Size
        self.target_length = target_length 
        self.ai_move_count = 0

    def get_move(self, board_grid, last_x=-1, last_y=-1, ai_color=2):
        """
        Main decision function.
        - ai_color: The color the Teacher is playing (usually 2/White)
        """
        self.ai_move_count += 1
        
        # 1. Opening: Play near the center or near the opponent for the first few moves
        # This prevents the AI from playing identically every game.
        if self.ai_move_count < 2 and last_x != -1:
            return self._smart_opening(board_grid, last_x, last_y)
        
        # 2. Evaluate Board State
        # Score my own attack potential
        score_self = self._evaluate_board(board_grid, ai_color)
        
        # Score opponent's threat level
        opponent_color = -ai_color if ai_color == 1 else 1 # Assuming 1 is P1
        if ai_color == 2: opponent_color = 1
        
        score_opponent = self._evaluate_board(board_grid, opponent_color)

        # 3. Find Best Move
        # We combine scores: Attack + (Defense * 1.2)
        # The 1.2 multiplier makes the teacher "Defensive" (Paranoid about losing)
        max_score = -1
        best_moves = []

        for x in range(self.level):
            for y in range(self.level):
                # Skip occupied spots
                if board_grid[x][y] != 0: continue
                
                # Total Score Formula
                total_score = score_self[x][y] + (score_opponent[x][y] * 1.2)
                
                if total_score > max_score:
                    max_score = total_score
                    best_moves = [(x, y)]
                elif total_score == max_score:
                    best_moves.append((x, y))
        
        # 4. Fallback (If board is full or empty)
        if not best_moves: 
            return self._find_random_empty(board_grid)
            
        # Pick a random best move to add variety
        return best_moves[randint(0, len(best_moves)-1)]

    def _evaluate_board(self, board, color):
        """Generates a score map for a specific player color."""
        scores = [[0 for _ in range(self.level)] for _ in range(self.level)]
        
        # Directions: Horizontal, Vertical, Diagonal \, Diagonal /
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for x in range(self.level):
            for y in range(self.level):
                # Optimization: Only calculate for empty spots near existing stones
                if board[x][y] != 0: continue 
                if not self._has_neighbor(board, x, y): continue

                for dx, dy in directions:
                    self._analyze_line(board, x, y, dx, dy, color, scores)
                    
        return scores

    def _analyze_line(self, board, x, y, dx, dy, color, scores):
        """
        Scans a specific line passing through (x,y) and assigns points.
        Logic adapted for 4-in-a-row.
        """
        # Count consecutive stones in positive direction
        count = 1 
        i, j = x + dx, y + dy
        while 0 <= i < self.level and 0 <= j < self.level and board[i][j] == color:
            count += 1
            i += dx
            j += dy
        # Check if the end is blocked or open
        open_end_1 = (0 <= i < self.level and 0 <= j < self.level and board[i][j] == 0)
        
        # Count consecutive stones in negative direction
        i, j = x - dx, y - dy
        while 0 <= i < self.level and 0 <= j < self.level and board[i][j] == color:
            count += 1
            i -= dx
            j -= dy
        open_end_2 = (0 <= i < self.level and 0 <= j < self.level and board[i][j] == 0)

        # --- SCORING RULES (The Brain) ---
        
        # 1. WIN (4 in a row)
        # If placing here makes 4, it's a win.
        if count >= 4:
            scores[x][y] += SCORE_WIN
            return

        # 2. LIVE 3 (_XXX_) -> This is a forced win in 4-row
        if count == 3 and open_end_1 and open_end_2:
            scores[x][y] += SCORE_LIVE_3
            return

        # 3. DEAD 3 (XXX_ or _XXX) -> A serious threat
        if count == 3 and (open_end_1 or open_end_2):
            scores[x][y] += SCORE_DEAD_3
            return

        # 4. LIVE 2 (_XX_) -> Good potential
        if count == 2 and open_end_1 and open_end_2:
            scores[x][y] += SCORE_LIVE_2
            return

        # 5. DEAD 2 (XX_ or _XX) -> Weak potential
        if count == 2 and (open_end_1 or open_end_2):
            scores[x][y] += SCORE_DEAD_2
            return

        # Bonus for just connecting
        scores[x][y] += count * 10

    def _has_neighbor(self, board, x, y):
        """Quick check: Does this empty spot have any stones around it?"""
        # Search radius 2 to catch disconnected threats (like X_X)
        for i in range(x-2, x+3):
            for j in range(y-2, y+3):
                if 0 <= i < self.level and 0 <= j < self.level:
                    if board[i][j] != 0: return True
        return False

    def _smart_opening(self, board, last_x, last_y):
        """Plays randomly near the last move to create diverse training games."""
        offsets = [
            (0,1), (0,-1), (1,0), (-1,0), 
            (1,1), (1,-1), (-1,1), (-1,-1)
        ]
        valid_moves = []
        for dx, dy in offsets:
            nx, ny = last_x + dx, last_y + dy
            if 0 <= nx < self.level and 0 <= ny < self.level and board[nx][ny] == 0:
                valid_moves.append((nx, ny))
        
        if valid_moves:
            return valid_moves[randint(0, len(valid_moves)-1)]
        return self._find_random_empty(board)

    def _find_random_empty(self, board):
        empty_spots = []
        for i in range(self.level):
            for j in range(self.level):
                if board[i][j] == 0:
                    empty_spots.append((i,j))
        if not empty_spots: return (-1, -1)
        return empty_spots[randint(0, len(empty_spots) - 1)]