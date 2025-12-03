def sudoku(grid: Matrix) -> Matrix | None:
    if location := find_empty_location(grid):
        row, column = location
    else:
        return grid

    for digit in range(1, 10):
        if is_safe(grid, row, column, digit):
            grid[row][column] = digit

            if sudoku(grid) is not None:
                return grid

            grid[row][column] = 0

    return None
