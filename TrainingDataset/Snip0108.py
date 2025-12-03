def find_empty_location(grid: Matrix) -> tuple[int, int] | None:
    
    for i in range(9):
        for j in range(9):
            if grid[i][j] == 0:
                return i, j
    return None
