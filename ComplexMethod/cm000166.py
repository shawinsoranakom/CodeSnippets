def compute_transform_tables(
    source_string: str,
    destination_string: str,
    copy_cost: int,
    replace_cost: int,
    delete_cost: int,
    insert_cost: int,
) -> tuple[list[list[int]], list[list[str]]]:
    """
    Finds the most cost efficient sequence
    for converting one string into another.

    >>> costs, operations = compute_transform_tables("cat", "cut", 1, 2, 3, 3)
    >>> costs[0][:4]
    [0, 3, 6, 9]
    >>> costs[2][:4]
    [6, 4, 3, 6]
    >>> operations[0][:4]
    ['0', 'Ic', 'Iu', 'It']
    >>> operations[3][:4]
    ['Dt', 'Dt', 'Rtu', 'Ct']

    >>> compute_transform_tables("", "", 1, 2, 3, 3)
    ([[0]], [['0']])
    """
    source_seq = list(source_string)
    destination_seq = list(destination_string)
    len_source_seq = len(source_seq)
    len_destination_seq = len(destination_seq)
    costs = [
        [0 for _ in range(len_destination_seq + 1)] for _ in range(len_source_seq + 1)
    ]
    ops = [
        ["0" for _ in range(len_destination_seq + 1)] for _ in range(len_source_seq + 1)
    ]

    for i in range(1, len_source_seq + 1):
        costs[i][0] = i * delete_cost
        ops[i][0] = f"D{source_seq[i - 1]}"

    for i in range(1, len_destination_seq + 1):
        costs[0][i] = i * insert_cost
        ops[0][i] = f"I{destination_seq[i - 1]}"

    for i in range(1, len_source_seq + 1):
        for j in range(1, len_destination_seq + 1):
            if source_seq[i - 1] == destination_seq[j - 1]:
                costs[i][j] = costs[i - 1][j - 1] + copy_cost
                ops[i][j] = f"C{source_seq[i - 1]}"
            else:
                costs[i][j] = costs[i - 1][j - 1] + replace_cost
                ops[i][j] = f"R{source_seq[i - 1]}" + str(destination_seq[j - 1])

            if costs[i - 1][j] + delete_cost < costs[i][j]:
                costs[i][j] = costs[i - 1][j] + delete_cost
                ops[i][j] = f"D{source_seq[i - 1]}"

            if costs[i][j - 1] + insert_cost < costs[i][j]:
                costs[i][j] = costs[i][j - 1] + insert_cost
                ops[i][j] = f"I{destination_seq[j - 1]}"

    return costs, ops