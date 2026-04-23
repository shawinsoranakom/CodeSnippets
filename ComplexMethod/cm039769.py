def expand_dims(
    a: Array, /, *, axis: int | tuple[int, ...] = (0,), xp: ModuleType | None = None
) -> Array:
    """
    Expand the shape of an array.

    Insert (a) new axis/axes that will appear at the position(s) specified by
    `axis` in the expanded array shape.

    This is ``xp.expand_dims`` for `axis` an int *or a tuple of ints*.
    Roughly equivalent to ``numpy.expand_dims`` for NumPy arrays.

    Parameters
    ----------
    a : array
        Array to have its shape expanded.
    axis : int or tuple of ints, optional
        Position(s) in the expanded axes where the new axis (or axes) is/are placed.
        If multiple positions are provided, they should be unique (note that a position
        given by a positive index could also be referred to by a negative index -
        that will also result in an error).
        Default: ``(0,)``.
    xp : array_namespace, optional
        The standard-compatible namespace for `a`. Default: infer.

    Returns
    -------
    array
        `a` with an expanded shape.

    Examples
    --------
    >>> import array_api_strict as xp
    >>> import array_api_extra as xpx
    >>> x = xp.asarray([1, 2])
    >>> x.shape
    (2,)

    The following is equivalent to ``x[xp.newaxis, :]`` or ``x[xp.newaxis]``:

    >>> y = xpx.expand_dims(x, axis=0, xp=xp)
    >>> y
    Array([[1, 2]], dtype=array_api_strict.int64)
    >>> y.shape
    (1, 2)

    The following is equivalent to ``x[:, xp.newaxis]``:

    >>> y = xpx.expand_dims(x, axis=1, xp=xp)
    >>> y
    Array([[1],
           [2]], dtype=array_api_strict.int64)
    >>> y.shape
    (2, 1)

    ``axis`` may also be a tuple:

    >>> y = xpx.expand_dims(x, axis=(0, 1), xp=xp)
    >>> y
    Array([[[1, 2]]], dtype=array_api_strict.int64)

    >>> y = xpx.expand_dims(x, axis=(2, 0), xp=xp)
    >>> y
    Array([[[1],
            [2]]], dtype=array_api_strict.int64)
    """
    if xp is None:
        xp = array_namespace(a)

    if not isinstance(axis, tuple):
        axis = (axis,)
    ndim = a.ndim + len(axis)
    if axis != () and (min(axis) < -ndim or max(axis) >= ndim):
        err_msg = (
            f"a provided axis position is out of bounds for array of dimension {a.ndim}"
        )
        raise IndexError(err_msg)
    axis = tuple(dim % ndim for dim in axis)
    if len(set(axis)) != len(axis):
        err_msg = "Duplicate dimensions specified in `axis`."
        raise ValueError(err_msg)
    for i in sorted(axis):
        a = xp.expand_dims(a, axis=i)
    return a