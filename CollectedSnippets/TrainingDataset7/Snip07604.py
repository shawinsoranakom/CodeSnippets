def bisect_keep_left(a, fn):
    """
    Find the index of the first element from the start of the array that
    verifies the given condition.
    The function is applied from the start of the array to the pivot.
    """
    lo = 0
    hi = len(a)
    while lo < hi:
        mid = (lo + hi) // 2
        if fn(a[: mid + 1]):
            hi = mid
        else:
            lo = mid + 1
    return lo