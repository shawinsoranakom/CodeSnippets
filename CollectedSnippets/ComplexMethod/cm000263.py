def depth_first_search(grid: list[list[int]], row: int, col: int, visit: set) -> int:
    """
    Recursive Backtracking Depth First Search Algorithm

    Starting from top left of a matrix, count the number of
    paths that can reach the bottom right of a matrix.
    1 represents a block (inaccessible)
    0 represents a valid space (accessible)

    0  0  0  0
    1  1  0  0
    0  0  0  1
    0  1  0  0
    >>> grid = [[0, 0, 0, 0], [1, 1, 0, 0], [0, 0, 0, 1], [0, 1, 0, 0]]
    >>> depth_first_search(grid, 0, 0, set())
    2

    0  0  0  0  0
    0  1  1  1  0
    0  1  1  1  0
    0  0  0  0  0
    >>> grid = [[0, 0, 0, 0, 0], [0, 1, 1, 1, 0], [0, 1, 1, 1, 0], [0, 0, 0, 0, 0]]
    >>> depth_first_search(grid, 0, 0, set())
    2
    """
    row_length, col_length = len(grid), len(grid[0])
    if (
        min(row, col) < 0
        or row == row_length
        or col == col_length
        or (row, col) in visit
        or grid[row][col] == 1
    ):
        return 0
    if row == row_length - 1 and col == col_length - 1:
        return 1

    visit.add((row, col))

    count = 0
    count += depth_first_search(grid, row + 1, col, visit)
    count += depth_first_search(grid, row - 1, col, visit)
    count += depth_first_search(grid, row, col + 1, visit)
    count += depth_first_search(grid, row, col - 1, visit)

    visit.remove((row, col))
    return count