def clip(
    x: Array,
    /,
    min: float | Array | None = None,
    max: float | Array | None = None,
    *,
    xp: Namespace,
    # TODO: np.clip has other ufunc kwargs
    out: Array | None = None,
) -> Array:
    def _isscalar(a: object) -> TypeIs[float | None]:
        return isinstance(a, int | float) or a is None

    min_shape = () if _isscalar(min) else min.shape
    max_shape = () if _isscalar(max) else max.shape

    wrapped_xp = array_namespace(x)

    result_shape = xp.broadcast_shapes(x.shape, min_shape, max_shape)

    # np.clip does type promotion but the array API clip requires that the
    # output have the same dtype as x. We do this instead of just downcasting
    # the result of xp.clip() to handle some corner cases better (e.g.,
    # avoiding uint64 -> float64 promotion).

    # Note: cases where min or max overflow (integer) or round (float) in the
    # wrong direction when downcasting to x.dtype are unspecified. This code
    # just does whatever NumPy does when it downcasts in the assignment, but
    # other behavior could be preferred, especially for integers. For example,
    # this code produces:

    # >>> clip(asarray(0, dtype=int8), asarray(128, dtype=int16), None)
    # -128

    # but an answer of 0 might be preferred. See
    # https://github.com/numpy/numpy/issues/24976 for more discussion on this issue.

    # At least handle the case of Python integers correctly (see
    # https://github.com/numpy/numpy/pull/26892).
    if wrapped_xp.isdtype(x.dtype, "integral"):
        if type(min) is int and min <= wrapped_xp.iinfo(x.dtype).min:
            min = None
        if type(max) is int and max >= wrapped_xp.iinfo(x.dtype).max:
            max = None

    dev = _get_device(x)
    if out is None:
        out = wrapped_xp.empty(result_shape, dtype=x.dtype, device=dev)
    assert out is not None  # workaround for a type-narrowing issue in pyright
    out[()] = x

    if min is not None:
        a = wrapped_xp.asarray(min, dtype=x.dtype, device=dev)
        a = xp.broadcast_to(a, result_shape)
        ia = (out < a) | xp.isnan(a)
        out[ia] = a[ia]

    if max is not None:
        b = wrapped_xp.asarray(max, dtype=x.dtype, device=dev)
        b = xp.broadcast_to(b, result_shape)
        ib = (out > b) | xp.isnan(b)
        out[ib] = b[ib]

    # Return a scalar for 0-D
    return out[()]