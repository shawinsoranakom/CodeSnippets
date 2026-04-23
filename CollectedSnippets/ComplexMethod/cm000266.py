def move_y(matrix_g: list[list[str]], size: int) -> list[list[str]]:
    """
    Shifts all columns leftward when an entire column becomes empty.

    >>> move_y([['-', 'A'], ['-', '-'], ['-', 'C']], 2)
    [['A', '-'], ['-', '-'], ['-', 'C']]
    """

    empty_columns = []

    for column in range(size - 1, -1, -1):
        if all(matrix_g[row][column] == "-" for row in range(size)):
            empty_columns.append(column)

    for column in empty_columns:
        for col in range(column + 1, size):
            for row in range(size):
                matrix_g[row][col - 1] = matrix_g[row][col]
        for row in range(size):
            matrix_g[row][-1] = "-"

    return matrix_g