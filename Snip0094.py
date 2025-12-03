def open_knight_tour(n: int) -> list[list[int]]:

    board = [[0 for i in range(n)] for j in range(n)]

    for i in range(n):
        for j in range(n):
            board[i][j] = 1
            if open_knight_tour_helper(board, (i, j), 1):
                return board
            board[i][j] = 0

    msg = f"Open Knight Tour cannot be performed on a board of size {n}"
    raise ValueError(msg)
