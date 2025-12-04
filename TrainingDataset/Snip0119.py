def word_exists(board: list[list[str]], word: str) -> bool:
  
    board_error_message = (
        "The board should be a non empty matrix of single chars strings."
    )

    len_board = len(board)
    if not isinstance(board, list) or len(board) == 0:
        raise ValueError(board_error_message)

    for row in board:
        if not isinstance(row, list) or len(row) == 0:
            raise ValueError(board_error_message)

        for item in row:
            if not isinstance(item, str) or len(item) != 1:
                raise ValueError(board_error_message)

    if not isinstance(word, str) or len(word) == 0:
        raise ValueError(
            "The word parameter should be a string of length greater than 0."
        )

    len_board_column = len(board[0])
    for i in range(len_board):
        for j in range(len_board_column):
            if exits_word(
                board, word, i, j, 0, {get_point_key(len_board, len_board_column, i, j)}
            ):
                return True

    return False
