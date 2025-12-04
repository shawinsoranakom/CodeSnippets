def get_point_key(len_board: int, len_board_column: int, row: int, column: int) -> int:
    
    return len_board * len_board_column * row + column
