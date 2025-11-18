# ai_player.py
# 包含 AIPlayer 類別

from random import randint
from constants import LEVEL, GRADE, MAX_SCORE

class AIPlayer:
    """封裝所有 AI 計算邏輯"""
    def __init__(self):
        self.level = LEVEL
        self.grade = GRADE
        self.MAX_SCORE = MAX_SCORE
        self.ai_move_count = 0 # 用於 BetaGo 的 times 變數

    def get_move(self, board_grid, last_move_x, last_move_y, ai_color):
        """
        AI 決策的主函式 (原來的 BetaGo)
        ai_color: AI 是 1 (黑) 還是 -1 (白)
        """
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
            print(f"AI 防守: ({max_x_P}, {max_y_P})")
            return max_x_P, max_y_P
        else:
            print(f"AI 進攻: ({max_x_AI}, {max_y_AI})")
            return max_x_AI, max_y_AI

    def _scan(self, chesspad, color):
        """(原來的 Scan 函式)"""
        shape = [[[0 for high in range(5)] for col in range(15)] for row in range(15)]
        for i in range(15):
            for j in range(15):
                if chesspad[i][j] == 0:
                    m, n = i, j
                    while n - 1 >= 0 and chesspad[m][n - 1] == color:
                        n -= 1
                        shape[i][j][0] += self.grade
                    if n - 1 >= 0 and chesspad[m][n - 1] == 0: shape[i][j][0] += 1
                    if n - 1 >= 0 and chesspad[m][n - 1] == -color: shape[i][j][0] -= 2
                    m, n = i, j
                    while (n + 1 < self.level and chesspad[m][n + 1] == color):
                        n += 1
                        shape[i][j][0] += self.grade
                    if n + 1 < self.level and chesspad[m][n + 1] == 0: shape[i][j][0] += 1
                    if n + 1 < self.level and chesspad[m][n + 1] == -color: shape[i][j][0] -= 2
                    m, n = i, j
                    while (m - 1 >= 0 and chesspad[m - 1][n] == color):
                        m -= 1
                        shape[i][j][1] += self.grade
                    if m - 1 >= 0 and chesspad[m - 1][n] == 0: shape[i][j][1] += 1
                    if m - 1 >= 0 and chesspad[m - 1][n] == -color: shape[i][j][1] -= 2
                    m, n = i, j
                    while (m + 1 < self.level and chesspad[m + 1][n] == color):
                        m += 1
                        shape[i][j][1] += self.grade
                    if m + 1 < self.level and chesspad[m + 1][n] == 0: shape[i][j][1] += 1
                    if m + 1 < self.level and chesspad[m + 1][n] == -color: shape[i][j][1] -= 2
                    m, n = i, j
                    while (m - 1 >= 0 and n + 1 < self.level and chesspad[m - 1][n + 1] == color):
                        m -= 1
                        n += 1
                        shape[i][j][2] += self.grade
                    if m - 1 >= 0 and n + 1 < self.level and chesspad[m - 1][n + 1] == 0: shape[i][j][2] += 1
                    if m - 1 >= 0 and n + 1 < self.level and chesspad[m - 1][n + 1] == -color: shape[i][j][2] -= 2
                    m, n = i, j
                    while (m + 1 < self.level and n - 1 >= 0 and chesspad[m + 1][n - 1] == color):
                        m += 1
                        n -= 1
                        shape[i][j][2] += self.grade
                    if m + 1 < self.level and n - 1 >= 0 and chesspad[m + 1][n - 1] == 0: shape[i][j][2] += 1
                    if m + 1 < self.level and n - 1 >= 0 and chesspad[m + 1][n - 1] == -color: shape[i][j][2] -= 2
                    m, n = i, j
                    while (m - 1 >= 0 and n - 1 >= 0 and chesspad[m - 1][n - 1] == color):
                        m -= 1
                        n -= 1
                        shape[i][j][3] += self.grade
                    if m - 1 >= 0 and n - 1 >= 0 and chesspad[m - 1][n - 1] == 0: shape[i][j][3] += 1
                    if m - 1 >= 0 and n - 1 >= 0 and chesspad[m - 1][n - 1] == -color: shape[i][j][3] -= 2
                    m, n = i, j
                    while m + 1 < self.level and n + 1 < self.level and chesspad[m + 1][n + 1] == color:
                        m += 1
                        n += 1
                        shape[i][j][3] += self.grade
                    if m + 1 < self.level and n + 1 < self.level and chesspad[m + 1][n + 1] == 0: shape[i][j][3] += 1
                    if m + 1 < self.level and n + 1 < self.level and chesspad[m + 1][n + 1] == -color: shape[i][j][3] -= 2
        return shape

    @staticmethod
    def _sort(shape):
        """(原來的 Sort 函式) 靜態方法，因為它不需要 self"""
        for i in shape:
            for j in i:
                for x in range(5):
                    for w in range(3, x - 1, -1):
                        if j[w - 1] < j[w]:
                            temp = j[w]
                            j[w - 1] = j[w]
                            j[w] = temp
        print("AI Sort Done !")
        return shape

    def _evaluate(self, shape):
        """(原來的 Evaluate 函式)"""
        for i in range(self.level):
            for j in range(self.level):
                if shape[i][j][0] == 4:
                    return i, j, self.MAX_SCORE
                shape[i][j][4] = shape[i][j][0] * 1000 + shape[i][j][1] * 100 + shape[i][j][2] * 10 + shape[i][j][3]
        
        max_x, max_y, max_val = 0, 0, 0
        
        for i in range(15):
            for j in range(15):
                if max_val < shape[i][j][4]:
                    max_val = shape[i][j][4]
                    max_x = i
                    max_y = j
        print(f"AI Evaluate max is {max_val} at ({max_x}, {max_y})")
        return max_x, max_y, max_val

    def _autoplay(self, ch, m, n):
        """(原來的 Autoplay 函式) 隨機找一個鄰近的空點"""
        a1 = [1, -1, 1, -1, 1, -1, 0, 0]
        b1 = [1, -1, -1, 1, 0, 0, 1, -1]
        rand = randint(0, 7)
        
        # 確保隨機點在棋盤內且為空
        while not (0 <= m + a1[rand] < self.level and 
                   0 <= n + b1[rand] < self.level and 
                   ch[m + a1[rand]][n + b1[rand]] == 0):
            rand = randint(0, 7)
            if all(not (0 <= m + a1[i] < self.level and 
                       0 <= n + b1[i] < self.level and 
                       ch[m + a1[i]][n + b1[i]] == 0) for i in range(8)):
                return self._find_random_empty(ch)

        return m + a1[rand], n + b1[rand]

    def _find_random_empty(self, ch):
        """隨機找一個棋盤上的空點 (用於 Autoplay 失敗時)"""
        empty_spots = []
        for i in range(self.level):
            for j in range(self.level):
                if ch[i][j] == 0:
                    empty_spots.append((i,j))
        if not empty_spots:
            return -1, -1 # 棋盤滿了
        return empty_spots[randint(0, len(empty_spots) - 1)]