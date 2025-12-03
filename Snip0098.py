def is_safe(board: list[list[int]], row: int, column: int) -> bool:

    n = len(board) 
    return (
        all(board[i][j] != 1 for i, j in zip(range(row), [column] * row))
        and all(
            board[i][j] != 1
            for i, j in zip(range(row - 1, -1, -1), range(column - 1, -1, -1))
        )
        and all(
            board[i][j] != 1
            for i, j in zip(range(row - 1, -1, -1), range(column + 1, n))
        )
    )
