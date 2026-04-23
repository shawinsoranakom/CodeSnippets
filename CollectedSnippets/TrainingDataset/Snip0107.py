def is_safe(grid: Matrix, row: int, column: int, n: int) -> bool:
    
    for i in range(9):
        if n in {grid[row][i], grid[i][column]}:
            return False

    for i in range(3):
        for j in range(3):
            if grid[(row - row % 3) + i][(column - column % 3) + j] == n:
                return False

    return True
