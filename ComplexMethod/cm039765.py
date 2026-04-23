def one_hot(
    x: Array,
    /,
    num_classes: int,
    *,
    dtype: DType | None = None,
    axis: int = -1,
    xp: ModuleType | None = None,
) -> Array:
    """
    One-hot encode the given indices.

    Each index in the input `x` is encoded as a vector of zeros of length `num_classes`
    with the element at the given index set to one.

    Parameters
    ----------
    x : array
        An array with integral dtype whose values are between `0` and `num_classes - 1`.
    num_classes : int
        Number of classes in the one-hot dimension.
    dtype : DType, optional
        The dtype of the return value.  Defaults to the default float dtype (usually
        float64).
    axis : int, optional
        Position in the expanded axes where the new axis is placed. Default: -1.
    xp : array_namespace, optional
        The standard-compatible namespace for `x`. Default: infer.

    Returns
    -------
    array
        An array having the same shape as `x` except for a new axis at the position
        given by `axis` having size `num_classes`.  If `axis` is unspecified, it
        defaults to -1, which appends a new axis.

        If ``x < 0`` or ``x >= num_classes``, then the result is undefined, may raise
        an exception, or may even cause a bad state.  `x` is not checked.

    Examples
    --------
    >>> import array_api_extra as xpx
    >>> import array_api_strict as xp
    >>> xpx.one_hot(xp.asarray([1, 2, 0]), 3)
    Array([[0., 1., 0.],
          [0., 0., 1.],
          [1., 0., 0.]], dtype=array_api_strict.float64)
    """
    # Validate inputs.
    if xp is None:
        xp = array_namespace(x)
    if not xp.isdtype(x.dtype, "integral"):
        msg = "x must have an integral dtype."
        raise TypeError(msg)
    if dtype is None:
        dtype = _funcs.default_dtype(xp, device=get_device(x))
    # Delegate where possible.
    if is_jax_namespace(xp):
        from jax.nn import one_hot as jax_one_hot

        return jax_one_hot(x, num_classes, dtype=dtype, axis=axis)
    if is_torch_namespace(xp):
        from torch.nn.functional import one_hot as torch_one_hot

        x = xp.astype(x, xp.int64)  # PyTorch only supports int64 here.
        try:
            out = torch_one_hot(x, num_classes)
        except RuntimeError as e:
            raise IndexError from e
    else:
        out = _funcs.one_hot(x, num_classes, xp=xp)
    out = xp.astype(out, dtype, copy=False)
    if axis != -1:
        out = xp.moveaxis(out, -1, axis)
    return out