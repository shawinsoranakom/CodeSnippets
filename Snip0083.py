def remove_word(
    puzzle: list[list[str]], word: str, row: int, col: int, vertical: bool
) -> None:
    
    for i in range(len(word)):
        if vertical:
            puzzle[row + i][col] = ""
        else:
            puzzle[row][col + i] = ""
