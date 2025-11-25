# go_engine.py
# Handles the specific rules of Go (Weiqi/Baduk): Liberties and Capturing.

class GoEngine:
    def __init__(self, board_grid):
        self.grid = board_grid
        self.rows = len(board_grid)
        self.cols = len(board_grid[0])
        # Track captured stones: 1=Black, -1=White
        self.prisoners = {1: 0, -1: 0} 

    def place_stone(self, r, c, color):
        """
        Attempts to place a stone.
        Returns:
            success (bool): True if valid, False if suicide/invalid.
            captured (list): List of (r, c) tuples of stones to remove.
        """
        if self.grid[r][c] != 0:
            return False, []

        # 1. Temporarily place the stone
        self.grid[r][c] = color
        opponent = -color
        captured_stones = []

        # 2. Check neighbors for captures (Opponent losing all liberties)
        neighbors = self._get_neighbors(r, c)
        for nr, nc in neighbors:
            if self.grid[nr][nc] == opponent:
                group = self._get_group(nr, nc)
                if self._count_liberties(group) == 0:
                    captured_stones.extend(group)

        # 3. Check for Suicide (If I have no liberties and captured nothing)
        if not captured_stones:
            my_group = self._get_group(r, c)
            if self._count_liberties(my_group) == 0:
                # Suicide rule: Illegal move
                self.grid[r][c] = 0 # Revert
                return False, []

        # 4. Apply Captures
        for cr, cc in captured_stones:
            self.grid[cr][cc] = 0
            
        # Track Prisoners (Captured stones add to the capturer's score)
        self.prisoners[color] += len(captured_stones)

        return True, captured_stones

    def calculate_score(self):
        """
        Calculates the final score based on Territory + Prisoners.
        Returns: (black_score, white_score)
        """
        black_territory = 0
        white_territory = 0
        
        visited = set()
        
        for r in range(self.rows):
            for c in range(self.cols):
                if self.grid[r][c] == 0 and (r, c) not in visited:
                    # Found an empty region, let's explore it
                    territory, owner = self._evaluate_territory(r, c, visited)
                    if owner == 1:
                        black_territory += territory
                    elif owner == -1:
                        white_territory += territory
                        
        # Total Score = Territory + Prisoners
        final_black = black_territory + self.prisoners[1]
        final_white = white_territory + self.prisoners[-1]
        
        return final_black, final_white

    def _evaluate_territory(self, start_r, start_c, visited):
        """
        Flood-fills an empty region to count its size and determine ownership.
        Returns: (size, owner)
        Owner: 1 (Black), -1 (White), 0 (Neutral/Both)
        """
        queue = [(start_r, start_c)]
        visited.add((start_r, start_c))
        territory_size = 0
        touched_colors = set()
        
        while queue:
            curr_r, curr_c = queue.pop(0)
            territory_size += 1
            
            for nr, nc in self._get_neighbors(curr_r, curr_c):
                if self.grid[nr][nc] == 0:
                    if (nr, nc) not in visited:
                        visited.add((nr, nc))
                        queue.append((nr, nc))
                else:
                    # We touched a stone! Remember its color.
                    touched_colors.add(self.grid[nr][nc])
        
        # Determine owner
        if len(touched_colors) == 1:
            return territory_size, list(touched_colors)[0] # Owned by one color
        else:
            return territory_size, 0 # Touched both or neither (Neutral)

    def _get_neighbors(self, r, c):
        offsets = [(-1, 0), (1, 0), (0, -1), (0, 1)]
        neighbors = []
        for dr, dc in offsets:
            nr, nc = r + dr, c + dc
            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                neighbors.append((nr, nc))
        return neighbors

    def _get_group(self, r, c):
        """Finds the connected group of stones of the same color."""
        color = self.grid[r][c]
        group = set([(r, c)])
        queue = [(r, c)]
        visited = set([(r, c)])

        while queue:
            curr_r, curr_c = queue.pop(0)
            for nr, nc in self._get_neighbors(curr_r, curr_c):
                if self.grid[nr][nc] == color and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    group.add((nr, nc))
                    queue.append((nr, nc))
        return list(group)

    def _count_liberties(self, group):
        """Counts empty spots adjacent to the entire group."""
        liberties = set()
        for r, c in group:
            for nr, nc in self._get_neighbors(r, c):
                if self.grid[nr][nc] == 0:
                    liberties.add((nr, nc))
        return len(liberties)