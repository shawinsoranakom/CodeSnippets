def slice_indices(slice, length):
    """
    Reference implementation for the slice.indices method.

    """
    # Compute step and length as integers.
    length = operator.index(length)
    step = 1 if slice.step is None else evaluate_slice_index(slice.step)

    # Raise ValueError for negative length or zero step.
    if length < 0:
        raise ValueError("length should not be negative")
    if step == 0:
        raise ValueError("slice step cannot be zero")

    # Find lower and upper bounds for start and stop.
    lower = -1 if step < 0 else 0
    upper = length - 1 if step < 0 else length

    # Compute start.
    if slice.start is None:
        start = upper if step < 0 else lower
    else:
        start = evaluate_slice_index(slice.start)
        start = max(start + length, lower) if start < 0 else min(start, upper)

    # Compute stop.
    if slice.stop is None:
        stop = lower if step < 0 else upper
    else:
        stop = evaluate_slice_index(slice.stop)
        stop = max(stop + length, lower) if stop < 0 else min(stop, upper)

    return start, stop, step