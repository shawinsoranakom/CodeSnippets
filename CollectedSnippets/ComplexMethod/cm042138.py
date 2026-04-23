def is_game_over(self) -> bool:
        for i in range(4):
            for j in range(4):
                if self.grid[i][j] == 0:
                    return False
                if j < 3 and self.grid[i][j] == self.grid[i][j + 1]:
                    return False
                if i < 3 and self.grid[i][j] == self.grid[i + 1][j]:
                    return False
        return True