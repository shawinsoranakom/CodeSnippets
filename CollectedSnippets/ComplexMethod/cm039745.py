def clip(
    x: Array,
    /,
    min: float | Array | None = None,
    max: float | Array | None = None,
) -> Array:
    """
    Array API compatibility wrapper for clip().

    See the corresponding documentation in the array library and/or the array API
    specification for more details.
    """

    def _isscalar(a: float | Array | None, /) -> TypeIs[float | None]:
        return a is None or isinstance(a, (int, float))

    min_shape = () if _isscalar(min) else min.shape
    max_shape = () if _isscalar(max) else max.shape

    # TODO: This won't handle dask unknown shapes
    result_shape = np.broadcast_shapes(x.shape, min_shape, max_shape)

    if min is not None:
        min = da.broadcast_to(da.asarray(min), result_shape)
    if max is not None:
        max = da.broadcast_to(da.asarray(max), result_shape)

    if min is None and max is None:
        return da.positive(x)

    if min is None:
        return astype(da.minimum(x, max), x.dtype)
    if max is None:
        return astype(da.maximum(x, min), x.dtype)

    return astype(da.minimum(da.maximum(x, min), max), x.dtype)