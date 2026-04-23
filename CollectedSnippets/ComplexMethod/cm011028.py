def _summarize_ranks(ranks: Iterable[int]) -> str:
    ranks = sorted(ranks)
    if min(ranks) < 0:
        raise AssertionError("ranks should all be positive")
    if len(set(ranks)) != len(ranks):
        raise AssertionError("ranks should not contain duplicates")
    curr: int | range | None = None
    ranges = []
    while ranks:
        x = ranks.pop(0)
        if curr is None:
            curr = x
        elif isinstance(curr, int):
            if x == curr + 1:
                curr = range(curr, x + 1, 1)
            else:
                step = x - curr
                curr = range(curr, x + step, step)
        else:
            if not isinstance(curr, range):
                raise AssertionError("curr must be an instance of range")
            if x == curr.stop:
                curr = range(curr.start, curr.stop + curr.step, curr.step)
            else:
                ranges.append(curr)
                curr = x

    if isinstance(curr, int):
        ranges.append(range(curr, curr + 1, 1))
    elif isinstance(curr, range):
        ranges.append(curr)

    result = []
    for r in ranges:
        if len(r) == 1:
            result.append(f"{r.start}")
        elif r.step == 1:
            result.append(f"{r.start}:{r.stop}")
        else:
            result.append(f"{r.start}:{r.stop}:{r.step}")
    return ",".join(result)