def solve(matrix: Matrix, vector: Matrix) -> Matrix:
    """
    Solve the linear system of equations Ax = b (A = "matrix", b = "vector")
    for x using Gaussian elimination and back substitution. We assume that A
    is an invertible square matrix and that b is a column vector of the
    same height.
    >>> solve([[1, 0], [0, 1]], [[1],[2]])
    [[1.0], [2.0]]
    >>> solve([[2, 1, -1],[-3, -1, 2],[-2, 1, 2]],[[8], [-11],[-3]])
    [[2.0], [3.0], [-1.0]]
    """
    size: int = len(matrix)
    augmented: Matrix = [[0 for _ in range(size + 1)] for _ in range(size)]
    row: int
    row2: int
    col: int
    col2: int
    pivot_row: int
    ratio: float

    for row in range(size):
        for col in range(size):
            augmented[row][col] = matrix[row][col]

        augmented[row][size] = vector[row][0]

    row = 0
    col = 0
    while row < size and col < size:
        # pivoting
        pivot_row = max((abs(augmented[row2][col]), row2) for row2 in range(col, size))[
            1
        ]
        if augmented[pivot_row][col] == 0:
            col += 1
            continue
        else:
            augmented[row], augmented[pivot_row] = augmented[pivot_row], augmented[row]

        for row2 in range(row + 1, size):
            ratio = augmented[row2][col] / augmented[row][col]
            augmented[row2][col] = 0
            for col2 in range(col + 1, size + 1):
                augmented[row2][col2] -= augmented[row][col2] * ratio

        row += 1
        col += 1

    # back substitution
    for col in range(1, size):
        for row in range(col):
            ratio = augmented[row][col] / augmented[col][col]
            for col2 in range(col, size + 1):
                augmented[row][col2] -= augmented[col][col2] * ratio

    # round to get rid of numbers like 2.000000000000004
    return [
        [round(augmented[row][size] / augmented[row][row], 10)] for row in range(size)
    ]