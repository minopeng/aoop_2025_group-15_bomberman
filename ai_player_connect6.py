# ai_player_connect6.py
# [專用版] 六子棋 (Connect 6) 演算法老師
# 懂得：連 6 顆才算贏，連 5 顆是致命威脅

from random import randint
from constants import LEVEL, GRADE, MAX_SCORE

class AIPlayer:
    """
    六子棋專用演算法 (Heuristic)
    Target: 6-in-a-row
    """
    def __init__(self, target_length=6):
        self.level = LEVEL
        self.grade = GRADE
        self.MAX_SCORE = MAX_SCORE
        self.ai_move_count = 0
        
        # [關鍵] 設定目標長度 (預設為 6)
        self.target_length = target_length 
        self.WIN_COUNT = self.target_length - 1 

    def get_move(self, board_grid, last_move_x, last_move_y, ai_color):
        self.ai_move_count += 1
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
        shape = [[[0 for high in range(5)] for col in range(15)] for row in range(15)]
        for i in range(self.level):
            for j in range(self.level):
                if chesspad[i][j] != 0: continue 

                # --- 1. 垂直 (Vertical) ---
                m, n = i, j
                count = 0
                while n - 1 >= 0 and chesspad[m][n - 1] == color:
                    n -= 1; count += 1
                up_space = (n - 1 >= 0 and chesspad[m][n - 1] == 0)
                
                m, n = i, j
                while n + 1 < self.level and chesspad[m][n + 1] == color:
                    n += 1; count += 1
                down_space = (n + 1 < self.level and chesspad[m][n + 1] == 0)
                self._score_shape(shape, i, j, 0, count, up_space, down_space)

                # --- 2. 水平 (Horizontal) ---
                m, n = i, j
                count = 0
                while m - 1 >= 0 and chesspad[m - 1][n] == color:
                    m -= 1; count += 1
                left_space = (m - 1 >= 0 and chesspad[m - 1][n] == 0)
                
                m, n = i, j
                while m + 1 < self.level and chesspad[m + 1][n] == color:
                    m += 1; count += 1
                right_space = (m + 1 < self.level and chesspad[m + 1][n] == 0)
                self._score_shape(shape, i, j, 1, count, left_space, right_space)

                # --- 3. 左下-右上 (Diagonal /) ---
                m, n = i, j
                count = 0
                while m - 1 >= 0 and n + 1 < self.level and chesspad[m - 1][n + 1] == color:
                    m -= 1; n += 1; count += 1
                dl_space = (m - 1 >= 0 and n + 1 < self.level and chesspad[m - 1][n + 1] == 0)
                
                m, n = i, j
                while m + 1 < self.level and n - 1 >= 0 and chesspad[m + 1][n - 1] == color:
                    m += 1; n -= 1; count += 1
                ur_space = (m + 1 < self.level and n - 1 >= 0 and chesspad[m + 1][n - 1] == 0)
                self._score_shape(shape, i, j, 2, count, dl_space, ur_space)

                # --- 4. 左上-右下 (Anti-Diagonal \) ---
                m, n = i, j
                count = 0
                while m - 1 >= 0 and n - 1 >= 0 and chesspad[m - 1][n - 1] == color:
                    m -= 1; n -= 1; count += 1
                ul_space = (m - 1 >= 0 and n - 1 >= 0 and chesspad[m - 1][n - 1] == 0)
                
                m, n = i, j
                while m + 1 < self.level and n + 1 < self.level and chesspad[m + 1][n + 1] == color:
                    m += 1; n += 1; count += 1
                dr_space = (m + 1 < self.level and n + 1 < self.level and chesspad[m + 1][n + 1] == 0)
                self._score_shape(shape, i, j, 3, count, ul_space, dr_space)

        return shape

    def _score_shape(self, shape, i, j, direction, count, open_1, open_2):
        """
        核心評分邏輯：針對六子棋 (Connect 6)
        """
        # [Case A] 已經連成 6 顆 (count >= 5) -> 必勝/必擋
        if count >= 5:
            shape[i][j][direction] += self.grade * 10000 
        # [Case B] 已經連成 5 顆 (count = 4) -> 極高威脅
        elif count == 4:
            shape[i][j][direction] += self.grade * 500
            if open_1: shape[i][j][direction] += 100
            if open_2: shape[i][j][direction] += 100
        # [Case C] 已經連成 4 顆 (count = 3) -> 進攻機會
        elif count == 3:
            shape[i][j][direction] += self.grade * 50
            if open_1: shape[i][j][direction] += 10
            if open_2: shape[i][j][direction] += 10
        # [Case D] 已經連成 3 顆 (count = 2) -> 佈局
        elif count == 2:
            shape[i][j][direction] += self.grade * 5
            if open_1: shape[i][j][direction] += 2
            if open_2: shape[i][j][direction] += 2
        # [Case E] 只有 1-2 顆 -> 基礎分
        elif count == 1:
            shape[i][j][direction] += 1

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
        for i in range(self.level):
            for j in range(self.level):
                if shape[i][j][0] >= (self.grade * 5000):
                    return i, j, self.MAX_SCORE
                shape[i][j][4] = (shape[i][j][0] * 1000 + shape[i][j][1] * 100 + shape[i][j][2] * 10 + shape[i][j][3])

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
            if 0 <= m+a1[rand] < self.level and 0 <= n+b1[rand] < self.level and ch[m+a1[rand]][n+b1[rand]] == 0:
                return m + a1[rand], n + b1[rand]
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
