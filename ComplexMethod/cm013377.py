def cross(a: ArrayLike, b: ArrayLike, axisa=-1, axisb=-1, axisc=-1, axis=None):
    # implementation vendored from
    # https://github.com/numpy/numpy/blob/v1.24.0/numpy/core/numeric.py#L1486-L1685
    if axis is not None:
        axisa, axisb, axisc = (axis,) * 3

    # Check axisa and axisb are within bounds
    axisa = _util.normalize_axis_index(axisa, a.ndim)
    axisb = _util.normalize_axis_index(axisb, b.ndim)

    # Move working axis to the end of the shape
    a = torch.moveaxis(a, axisa, -1)
    b = torch.moveaxis(b, axisb, -1)
    msg = "incompatible dimensions for cross product\n(dimension must be 2 or 3)"
    if a.shape[-1] not in (2, 3) or b.shape[-1] not in (2, 3):
        raise ValueError(msg)

    # Create the output array
    shape = broadcast_shapes(a[..., 0].shape, b[..., 0].shape)
    if a.shape[-1] == 3 or b.shape[-1] == 3:
        shape += (3,)
        # Check axisc is within bounds
        axisc = _util.normalize_axis_index(axisc, len(shape))
    dtype = _dtypes_impl.result_type_impl(a, b)
    cp = torch.empty(shape, dtype=dtype)

    # recast arrays as dtype
    a = _util.cast_if_needed(a, dtype)
    b = _util.cast_if_needed(b, dtype)

    # create local aliases for readability
    a0 = a[..., 0]
    a1 = a[..., 1]
    if a.shape[-1] == 3:
        a2 = a[..., 2]
    b0 = b[..., 0]
    b1 = b[..., 1]
    if b.shape[-1] == 3:
        b2 = b[..., 2]
    if cp.ndim != 0 and cp.shape[-1] == 3:
        cp0 = cp[..., 0]
        cp1 = cp[..., 1]
        cp2 = cp[..., 2]

    if a.shape[-1] == 2:
        if b.shape[-1] == 2:
            # a0 * b1 - a1 * b0
            cp[...] = a0 * b1 - a1 * b0
            return cp
        else:
            if b.shape[-1] != 3:
                raise AssertionError(f"b.shape[-1] must be 3, got {b.shape[-1]}")
            # cp0 = a1 * b2 - 0  (a2 = 0)
            # cp1 = 0 - a0 * b2  (a2 = 0)
            # cp2 = a0 * b1 - a1 * b0
            cp0[...] = a1 * b2
            cp1[...] = -a0 * b2
            cp2[...] = a0 * b1 - a1 * b0
    else:
        if a.shape[-1] != 3:
            raise AssertionError(f"a.shape[-1] must be 3, got {a.shape[-1]}")
        if b.shape[-1] == 3:
            cp0[...] = a1 * b2 - a2 * b1
            cp1[...] = a2 * b0 - a0 * b2
            cp2[...] = a0 * b1 - a1 * b0
        else:
            if b.shape[-1] != 2:
                raise AssertionError(f"b.shape[-1] must be 2, got {b.shape[-1]}")
            cp0[...] = -a2 * b1
            cp1[...] = a2 * b0
            cp2[...] = a0 * b1 - a1 * b0

    return torch.moveaxis(cp, -1, axisc)