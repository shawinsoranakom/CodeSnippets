def reduce_shape(shape, axis=None, keepdims=False):
    shape = list(shape)
    if axis is None:
        if keepdims:
            return tuple([1 for _ in shape])
        else:
            return tuple([])
    elif isinstance(axis, int):
        axis = (axis,)

    axis = tuple(canonicalize_axis(a, len(shape)) for a in axis)

    if keepdims:
        for ax in axis:
            shape[ax] = 1
        return tuple(shape)
    else:
        for ax in sorted(axis, reverse=True):
            del shape[ax]
        return tuple(shape)