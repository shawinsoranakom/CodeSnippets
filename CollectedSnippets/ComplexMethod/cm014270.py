def set_difference(
    set1: set[T],
    *others: Iterable[T],
    cls: type[Any] = set,
) -> Any:
    if len(others) == 0:
        return set1.copy()

    if not all(isinstance(s, Iterable) for s in others):
        raise TypeError(f"set.difference expected an iterable, got {type(others)}")

    for s in others:
        if any(not isinstance(x, Hashable) for x in s):
            raise TypeError("unhashable type")

    difference_set = set()
    for x in set1:
        for set2 in others:
            if x in set2:
                break
        else:
            difference_set.add(x)
    return cls(difference_set)