def partition(predicate, values):
    """
    Split the values into two sets, based on the return value of the function
    (True/False). e.g.:

        >>> partition(lambda x: x > 3, range(5))
        [0, 1, 2, 3], [4]
    """
    results = ([], [])
    for item in values:
        results[predicate(item)].append(item)
    return results