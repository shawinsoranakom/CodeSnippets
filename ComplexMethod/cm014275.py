def islice(iterable: Iterable[_T], /, *args: int | None) -> Iterator[_T]:
    s = slice(*args)
    start = 0 if s.start is None else s.start
    stop = s.stop
    step = 1 if s.step is None else s.step
    if start < 0 or (stop is not None and stop < 0) or step <= 0:
        raise ValueError(
            "Indices for islice() must be None or an integer: 0 <= x <= sys.maxsize.",
        )

    if stop is None:
        # TODO: use indices = itertools.count() and merge implementation with the else branch
        #       when we support infinite iterators
        next_i = start
        for i, element in enumerate(iterable):
            if i == next_i:
                yield element
                next_i += step
    else:
        indices = range(max(start, stop))
        next_i = start
        for i, element in zip(indices, iterable):
            if i == next_i:
                yield element
                next_i += step