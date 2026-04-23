def get_position(table: tuple[str, str], char: str) -> tuple[int, int]:
    row = 0 if char in table[0] else 1
    col = table[row].index(char)
    return row, col
