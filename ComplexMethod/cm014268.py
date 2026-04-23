def set_intersection(
    set1: set[T],
    *others: Iterable[T],
    # See facebook/pyrefly#1496 - leave generic
    cls: type[Any] = set,
) -> Any:
    if len(others) == 0:
        return set1.copy()

    if not all(isinstance(s, Iterable) for s in others):
        raise TypeError(f"set.difference expected an iterable, got {type(others)}")

    for s in others:
        if any(not isinstance(x, Hashable) for x in s):
            raise TypeError("unhashable type")

    # return a new set with elements common in all sets
    intersection_set = set()
    for x in set1:
        for set2 in others:
            if not any(x == y for y in set2):
                break
        else:
            intersection_set.add(x)
    return cls(intersection_set)