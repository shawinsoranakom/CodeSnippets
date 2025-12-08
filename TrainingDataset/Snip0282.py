def encrypt(input_string: str, key: int) -> str:
    temp_grid: list[list[str]] = [[] for _ in range(key)]
    lowest = key - 1

    if key <= 0:
        raise ValueError("Height of grid can't be 0 or negative")
    if key == 1 or len(input_string) <= key:
        return input_string

    for position, character in enumerate(input_string):
        num = position % (lowest * 2)  
        num = min(num, lowest * 2 - num) 
        temp_grid[num].append(character)
    grid = ["".join(row) for row in temp_grid]
    output_string = "".join(grid)

    return output_string
