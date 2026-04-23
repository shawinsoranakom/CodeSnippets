def get_valid_pos(position: tuple[int, int], n: int) -> list[tuple[int, int]]:
    
    y, x = position
    positions = [
        (y + 1, x + 2),
        (y - 1, x + 2),
        (y + 1, x - 2),
        (y - 1, x - 2),
        (y + 2, x + 1),
        (y + 2, x - 1),
        (y - 2, x + 1),
        (y - 2, x - 1),
    ]
    permissible_positions = []

    for inner_position in positions:
        y_test, x_test = inner_position
        if 0 <= y_test < n and 0 <= x_test < n:
            permissible_positions.append(inner_position)

    return permissible_positions
