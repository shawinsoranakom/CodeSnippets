def combination_lists(n: int, k: int) -> list[list[int]]:
    """
    Generates all possible combinations of k numbers out of 1 ... n using itertools.

    >>> combination_lists(n=4, k=2)
    [[1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]
    """
    return [list(x) for x in combinations(range(1, n + 1), k)]
