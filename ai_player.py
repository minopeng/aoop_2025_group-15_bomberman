# ai_player.py
######################################################################
from random import randint
from constants import LEVEL, GRADE, MAX_SCORE

class AIPlayer:
    def __init__(self, target_length=5):
        self.level = LEVEL
        self.grade = GRADE
        self.MAX_SCORE = MAX_SCORE
        self.ai_move_count = 0
        self.target_length = 5 
        self.WIN_LEN = 5
        self.THREAT_LEN = 4

    def get_move(self, board_grid, last_move_x, last_move_y, ai_color):
        self.ai_move_count += 1
        
        if self.ai_move_count < 2:
            return self._autoplay(board_grid, last_move_x, last_move_y)
        
        score_self = self._evaluate_board(board_grid, ai_color)
        
        score_opponent = self._evaluate_board(board_grid, -ai_color)

        best_move = self._get_best_move(score_self, score_opponent)
        
        if best_move is None:
            return self._autoplay(board_grid, last_move_x, last_move_y)
            
        return best_move

    def _evaluate_board(self, board, color):
        scores = [[0 for _ in range(self.level)] for _ in range(self.level)]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for x in range(self.level):
            for y in range(self.level):
                if board[x][y] != 0: continue 

                for dx, dy in directions:
                    self._analyze_line(board, x, y, dx, dy, color, scores)
                    
        return scores

    def _analyze_line(self, board, x, y, dx, dy, color, scores):
        count = 1 
        i, j = x + dx, y + dy
        while 0 <= i < self.level and 0 <= j < self.level and board[i][j] == color:
            count += 1
            i += dx
            j += dy
        open_end_1 = (0 <= i < self.level and 0 <= j < self.level and board[i][j] == 0)
        
        i, j = x - dx, y - dy
        while 0 <= i < self.level and 0 <= j < self.level and board[i][j] == color:
            count += 1
            i -= dx
            j -= dy
        open_end_2 = (0 <= i < self.level and 0 <= j < self.level and board[i][j] == 0)

        if count >= 5:
            scores[x][y] += 100000
            return

        if count == 4 and open_end_1 and open_end_2:
            scores[x][y] += 10000 
            return

        if count == 4 and (open_end_1 or open_end_2):
            scores[x][y] += 1000 
            return

        if count == 3 and open_end_1 and open_end_2:
            scores[x][y] += 1000 
            return

        if count == 3 and (open_end_1 or open_end_2):
            scores[x][y] += 100
            return
            
        if count == 2 and open_end_1 and open_end_2:
            scores[x][y] += 50
            return

        scores[x][y] += count * 10

    def _get_best_move(self, score_self, score_opponent):
        max_score = -1
        best_moves = []

        for x in range(self.level):
            for y in range(self.level):
                total_score = score_self[x][y] + (score_opponent[x][y] * 1.2)
                
                if total_score > max_score:
                    max_score = total_score
                    best_moves = [(x, y)]
                elif total_score == max_score:
                    best_moves.append((x, y))
        
        if not best_moves: return None
        
        return best_moves[randint(0, len(best_moves)-1)]

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
