def string_overlap(a: str, b: str) -> tuple[Indices | None, Indices | None]:
    """
    Find the longest overlap where the end of string a matches the start
    of string b.

    Args:
        a: First string
        b: Second string

    Returns:
        Tuple of IndicesTuples representing the overlapping portions in each
        string, or a tuple of None if no overlap exists
    """

    # swap so a is always the shorter string
    a, b, swap = (a, b, False) if len(a) < len(b) else (b, a, True)

    # first check: is a fully contained in b?
    if a in b:
        ind_a = Indices(0, len(a))
        ind_b = Indices(b.index(a), b.index(a) + len(a))
        return (ind_b, ind_a) if swap else (ind_a, ind_b)

    # second check: does the end of a overlap with the
    #               beginning of b?
    for i in range(len(a) - 1, 0, -1):
        if a[-i:] == b[:i]:
            ind_a = Indices(len(a) - i, len(a))
            ind_b = Indices(0, i)
            return (ind_b, ind_a) if swap else (ind_a, ind_b)

    # third check: does the beginning of a overlap with
    #              the end of b?
    for i in range(len(a) - 1, 0, -1):
        if b[-i:] == a[:i]:
            ind_a = Indices(0, i)
            ind_b = Indices(len(b) - i, len(b))
            return (ind_b, ind_a) if swap else (ind_a, ind_b)

    return None, None