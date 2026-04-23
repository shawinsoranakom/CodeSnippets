def solve_simultaneous(equations: list[list]) -> list:
    """
    >>> solve_simultaneous([[1, 2, 3],[4, 5, 6]])
    [-1.0, 2.0]
    >>> solve_simultaneous([[0, -3, 1, 7],[3, 2, -1, 11],[5, 1, -2, 12]])
    [6.4, 1.2, 10.6]
    >>> solve_simultaneous([])
    Traceback (most recent call last):
        ...
    IndexError: solve_simultaneous() requires n lists of length n+1
    >>> solve_simultaneous([[1, 2, 3],[1, 2]])
    Traceback (most recent call last):
        ...
    IndexError: solve_simultaneous() requires n lists of length n+1
    >>> solve_simultaneous([[1, 2, 3],["a", 7, 8]])
    Traceback (most recent call last):
        ...
    ValueError: solve_simultaneous() requires lists of integers
    >>> solve_simultaneous([[0, 2, 3],[4, 0, 6]])
    Traceback (most recent call last):
        ...
    ValueError: solve_simultaneous() requires at least 1 full equation
    """
    if len(equations) == 0:
        raise IndexError("solve_simultaneous() requires n lists of length n+1")
    _length = len(equations) + 1
    if any(len(item) != _length for item in equations):
        raise IndexError("solve_simultaneous() requires n lists of length n+1")
    for row in equations:
        if any(not isinstance(column, (int, float)) for column in row):
            raise ValueError("solve_simultaneous() requires lists of integers")
    if len(equations) == 1:
        return [equations[0][-1] / equations[0][0]]
    data_set = equations.copy()
    if any(0 in row for row in data_set):
        temp_data = data_set.copy()
        full_row = []
        for row_index, row in enumerate(temp_data):
            if 0 not in row:
                full_row = data_set.pop(row_index)
                break
        if not full_row:
            raise ValueError("solve_simultaneous() requires at least 1 full equation")
        data_set.insert(0, full_row)
    useable_form = data_set.copy()
    simplified = simplify(useable_form)
    simplified = simplified[::-1]
    solutions: list = []
    for row in simplified:
        current_solution = row[-1]
        if not solutions:
            if row[-2] == 0:
                solutions.append(0)
                continue
            solutions.append(current_solution / row[-2])
            continue
        temp_row = row.copy()[: len(row) - 1 :]
        while temp_row[0] == 0:
            temp_row.pop(0)
        if len(temp_row) == 0:
            solutions.append(0)
            continue
        temp_row = temp_row[1::]
        temp_row = temp_row[::-1]
        for column_index, column in enumerate(temp_row):
            current_solution -= column * solutions[column_index]
        solutions.append(current_solution)
    final = []
    for item in solutions:
        final.append(float(round(item, 5)))
    return final[::-1]