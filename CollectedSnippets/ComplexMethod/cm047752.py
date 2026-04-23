def invert_intervals(intervals: Iterable[tuple[T, T]], first_start: T, last_stop: T) -> list[tuple[T, T]]:
    """Return the intervals between the intervals that were passed in.

    The expected use case is to turn "available intervals" into "unavailable intervals".
    :examples:
    ([(1, 2), (4, 5)], 0, 10) -> [(0, 1), (2, 4), (5, 10)]

    :param intervals:
    :param first_start: start of whole interval
    :param last_stop: stop of whole interval
    """
    items = []
    prev_stop = first_start
    for start, stop in sorted(intervals):
        if prev_stop and prev_stop < start and start <= last_stop:
            items.append((prev_stop, start))
        prev_stop = max(prev_stop, stop)
    if last_stop and prev_stop < last_stop:
        items.append((prev_stop, last_stop))
    # abuse Intervals to merge contiguous intervals
    return [(start, stop) for start, stop, _ in Intervals([(start, stop, set()) for start, stop in items])]