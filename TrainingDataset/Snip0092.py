def is_complete(board: list[list[int]]) -> bool:

    return not any(elem == 0 for row in board for elem in row)
