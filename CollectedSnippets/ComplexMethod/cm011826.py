def _validate_reduction_axis(x, axis):
    size = x.get_size()
    if isinstance(axis, int):
        axis = [axis]
    elif not axis:
        axis = range(len(size))
    if len(size) == 0:
        assert tuple(axis) in [(), (0,), (-1,)], f"invalid axis: {axis}"
        return []
    axis = list(axis)
    for i in range(len(axis)):
        if axis[i] < 0:
            axis[i] += len(size) if len(size) else 1
        assert 0 <= axis[i] < len(size) or (len(size) == 0 and axis[i] == 0)
    assert len(OrderedSet(axis)) == len(axis), "reduction axis not unique"
    return axis