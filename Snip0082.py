def place_word(
    puzzle: list[list[str]], word: str, row: int, col: int, vertical: bool
) -> None:
    
    for i, char in enumerate(word):
        if vertical:
            puzzle[row + i][col] = char
        else:
            puzzle[row][col + i] = char
