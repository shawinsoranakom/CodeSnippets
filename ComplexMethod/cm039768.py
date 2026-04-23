def broadcast_shapes(*shapes: tuple[float | None, ...]) -> tuple[int | None, ...]:
    """
    Compute the shape of the broadcasted arrays.

    Duplicates :func:`numpy.broadcast_shapes`, with additional support for
    None and NaN sizes.

    This is equivalent to ``xp.broadcast_arrays(arr1, arr2, ...)[0].shape``
    without needing to worry about the backend potentially deep copying
    the arrays.

    Parameters
    ----------
    *shapes : tuple[int | None, ...]
        Shapes of the arrays to broadcast.

    Returns
    -------
    tuple[int | None, ...]
        The shape of the broadcasted arrays.

    See Also
    --------
    numpy.broadcast_shapes : Equivalent NumPy function.
    array_api.broadcast_arrays : Function to broadcast actual arrays.

    Notes
    -----
    This function accepts the Array API's ``None`` for unknown sizes,
    as well as Dask's non-standard ``math.nan``.
    Regardless of input, the output always contains ``None`` for unknown sizes.

    Examples
    --------
    >>> import array_api_extra as xpx
    >>> xpx.broadcast_shapes((2, 3), (2, 1))
    (2, 3)
    >>> xpx.broadcast_shapes((4, 2, 3), (2, 1), (1, 3))
    (4, 2, 3)
    """
    if not shapes:
        return ()  # Match NumPy output

    ndim = max(len(shape) for shape in shapes)
    out: list[int | None] = []
    for axis in range(-ndim, 0):
        sizes = {shape[axis] for shape in shapes if axis >= -len(shape)}
        # Dask uses NaN for unknown shape, which predates the Array API spec for None
        none_size = None in sizes or math.nan in sizes  # noqa: PLW0177
        sizes -= {1, None, math.nan}
        if len(sizes) > 1:
            msg = (
                "shape mismatch: objects cannot be broadcast to a single shape: "
                f"{shapes}."
            )
            raise ValueError(msg)
        out.append(None if none_size else cast(int, sizes.pop()) if sizes else 1)

    return tuple(out)