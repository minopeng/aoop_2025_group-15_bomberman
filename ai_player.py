# ai_player.py
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
        """
        AI 決策的主函式
        """
        self.ai_move_count += 1
        
        if self.ai_move_count < 2:
            return self._autoplay(board_grid, last_move_x, last_move_y)
        
        score_self = self._evaluate_board(board_grid, ai_color)
        
        # 2. 掃描對手 (防守分數)
        score_opponent = self._evaluate_board(board_grid, -ai_color)

        # 3. 綜合評估
        best_move = self._get_best_move(score_self, score_opponent)
        
        if best_move is None:
            return self._autoplay(board_grid, last_move_x, last_move_y)
            
        return best_move

    def _evaluate_board(self, board, color):
        """評估棋盤上每一個空位的價值"""
        scores = [[0 for _ in range(self.level)] for _ in range(self.level)]
        directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

        for x in range(self.level):
            for y in range(self.level):
                if board[x][y] != 0: continue # 只評估空位

                for dx, dy in directions:
                    self._analyze_line(board, x, y, dx, dy, color, scores)
                    
        return scores

    def _analyze_line(self, board, x, y, dx, dy, color, scores):
        """
        分析單一線上的形狀 (活/死/衝)
        核心：五子棋規則
        """
        count = 1 # 包含(x,y)自己
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

        # --- [精準評分] 五子棋專用 ---
        
        # 1. 成五 (Win): 連成 5 顆 -> 贏了
        if count >= 5:
            scores[x][y] += 100000
            return

        # 2. 活四 (Live 4): 兩頭空 (_XXXX_) -> 下一步必勝
        if count == 4 and open_end_1 and open_end_2:
            scores[x][y] += 10000 # 必須擋/必須下
            return

        # 3. 死四 (Dead 4/Rush 4): 一頭空 (XXXX_) -> 必須擋
        if count == 4 and (open_end_1 or open_end_2):
            scores[x][y] += 1000 
            return
        # 4. 活三 (Live 3): 兩頭空 (_XXX_) -> 做成活四的基礎
        if count == 3 and open_end_1 and open_end_2:
            scores[x][y] += 1000 # 威脅很大，僅次於死四
            return

        # 5. 死三 (Dead 3): 一頭空 (XXX_)
        if count == 3 and (open_end_1 or open_end_2):
            scores[x][y] += 100
            return
            
        # 6. 活二 (Live 2): (_XX_)
        if count == 2 and open_end_1 and open_end_2:
            scores[x][y] += 50
            return

        # 基礎連接分
        scores[x][y] += count * 10

    def _get_best_move(self, score_self, score_opponent):
        max_score = -1
        best_moves = []

        for x in range(self.level):
            for y in range(self.level):
                # 總分 = 自己的進攻分 + (對手的威脅分 * 防守係數)
                # 防守係數 1.2：稍微偏向防守，因為五子棋只要漏擋一次就輸了
                total_score = score_self[x][y] + (score_opponent[x][y] * 1.2)
                
                if total_score > max_score:
                    max_score = total_score
                    best_moves = [(x, y)]
                elif total_score == max_score:
                    best_moves.append((x, y))
        
        if not best_moves: return None
        
        # 如果有多個同分點，隨機選一個 (增加變化，避免被背譜)
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
