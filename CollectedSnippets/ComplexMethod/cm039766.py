def pad(
    x: Array,
    pad_width: int | tuple[int, int] | Sequence[tuple[int, int]],
    mode: Literal["constant"] = "constant",
    *,
    constant_values: complex = 0,
    xp: ModuleType | None = None,
) -> Array:
    """
    Pad the input array.

    Parameters
    ----------
    x : array
        Input array.
    pad_width : int or tuple of ints or sequence of pairs of ints
        Pad the input array with this many elements from each side.
        If a sequence of tuples, ``[(before_0, after_0), ... (before_N, after_N)]``,
        each pair applies to the corresponding axis of ``x``.
        A single tuple, ``(before, after)``, is equivalent to a list of ``x.ndim``
        copies of this tuple.
    mode : str, optional
        Only "constant" mode is currently supported, which pads with
        the value passed to `constant_values`.
    constant_values : python scalar, optional
        Use this value to pad the input. Default is zero.
    xp : array_namespace, optional
        The standard-compatible namespace for `x`. Default: infer.

    Returns
    -------
    array
        The input array,
        padded with ``pad_width`` elements equal to ``constant_values``.
    """
    xp = array_namespace(x) if xp is None else xp

    if mode != "constant":
        msg = "Only `'constant'` mode is currently supported"
        raise NotImplementedError(msg)

    if (
        is_numpy_namespace(xp)
        or is_cupy_namespace(xp)
        or is_jax_namespace(xp)
        or is_pydata_sparse_namespace(xp)
    ):
        return xp.pad(x, pad_width, mode, constant_values=constant_values)

    # https://github.com/pytorch/pytorch/blob/cf76c05b4dc629ac989d1fb8e789d4fac04a095a/torch/_numpy/_funcs_impl.py#L2045-L2056
    if is_torch_namespace(xp):
        pad_width = xp.asarray(pad_width)
        pad_width = xp.broadcast_to(pad_width, (x.ndim, 2))
        pad_width = xp.flip(pad_width, axis=(0,)).flatten()
        return xp.nn.functional.pad(x, tuple(pad_width), value=constant_values)  # type: ignore[arg-type]  # pyright: ignore[reportArgumentType]

    return _funcs.pad(x, pad_width, constant_values=constant_values, xp=xp)