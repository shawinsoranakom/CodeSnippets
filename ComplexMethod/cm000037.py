def simplify(current_set: list[list]) -> list[list]:
    """
    >>> simplify([[1, 2, 3], [4, 5, 6]])
    [[1.0, 2.0, 3.0], [0.0, 0.75, 1.5]]
    >>> simplify([[5, 2, 5], [5, 1, 10]])
    [[1.0, 0.4, 1.0], [0.0, 0.2, -1.0]]
    """
    # Divide each row by magnitude of first term --> creates 'unit' matrix
    duplicate_set = current_set.copy()
    for row_index, row in enumerate(duplicate_set):
        magnitude = row[0]
        for column_index, column in enumerate(row):
            if magnitude == 0:
                current_set[row_index][column_index] = column
                continue
            current_set[row_index][column_index] = column / magnitude
    # Subtract to cancel term
    first_row = current_set[0]
    final_set = [first_row]
    current_set = current_set[1::]
    for row in current_set:
        temp_row = []
        # If first term is 0, it is already in form we want, so we preserve it
        if row[0] == 0:
            final_set.append(row)
            continue
        for column_index in range(len(row)):
            temp_row.append(first_row[column_index] - row[column_index])
        final_set.append(temp_row)
    # Create next recursion iteration set
    if len(final_set[0]) != 3:
        current_first_row = final_set[0]
        current_first_column = []
        next_iteration = []
        for row in final_set[1::]:
            current_first_column.append(row[0])
            next_iteration.append(row[1::])
        resultant = simplify(next_iteration)
        for i in range(len(resultant)):
            resultant[i].insert(0, current_first_column[i])
        resultant.insert(0, current_first_row)
        final_set = resultant
    return final_set