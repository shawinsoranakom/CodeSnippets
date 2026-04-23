def semi_perfect(number: int) -> bool:
    """
    >>> semi_perfect(0)
    True
    >>> semi_perfect(1)
    True
    >>> semi_perfect(12)
    True
    >>> semi_perfect(13)
    False

    # >>> semi_perfect(-12)
    # True
    """
    values = factors(number)
    r = len(values)
    subset = [[0 for i in range(number + 1)] for j in range(r + 1)]
    for i in range(r + 1):
        subset[i][0] = True

    for i in range(1, number + 1):
        subset[0][i] = False

    for i in range(1, r + 1):
        for j in range(1, number + 1):
            if j < values[i - 1]:
                subset[i][j] = subset[i - 1][j]
            else:
                subset[i][j] = subset[i - 1][j] or subset[i - 1][j - values[i - 1]]

    return subset[r][number] != 0