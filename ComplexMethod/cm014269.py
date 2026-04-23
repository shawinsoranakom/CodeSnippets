def set_union(
    set1: set[T], *others: Iterable[T], cls: type[C] | None = None
) -> C | set[T]:
    # frozenset also uses this function
    if cls is None:
        # pyrefly: ignore[bad-assignment]
        cls = type(set1)

    if len(others) == 0:
        return set1.copy()

    if not all(isinstance(s, Iterable) for s in others):
        raise TypeError(f"set.union expected an iterable, got {type(others)}")

    for s in others:
        if any(not isinstance(x, Hashable) for x in s):
            raise TypeError("unhashable type")

    union_set = set(set1.copy())
    for set2 in others:
        set_update(union_set, set2)

    # frozenset also uses this function
    # pyrefly: ignore [bad-argument-count, not-callable]
    return cls(union_set)