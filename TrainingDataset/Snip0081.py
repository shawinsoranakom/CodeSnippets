def is_valid(
    puzzle: list[list[str]], word: str, row: int, col: int, vertical: bool
) -> bool:
    
    for i in range(len(word)):
        if vertical:
            if row + i >= len(puzzle) or puzzle[row + i][col] != "":
                return False
        elif col + i >= len(puzzle[0]) or puzzle[row][col + i] != "":
            return False
    return True
