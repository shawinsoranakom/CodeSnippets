def pad(
    x: Array,
    pad_width: int | tuple[int, int] | Sequence[tuple[int, int]],
    *,
    constant_values: complex = 0,
    xp: ModuleType,
) -> Array:  # numpydoc ignore=PR01,RT01
    """See docstring in `array_api_extra._delegation.py`."""
    # make pad_width a list of length-2 tuples of ints
    if isinstance(pad_width, int):
        pad_width_seq = [(pad_width, pad_width)] * x.ndim
    elif (
        isinstance(pad_width, tuple)
        and len(pad_width) == 2
        and all(isinstance(i, int) for i in pad_width)
    ):
        pad_width_seq = [cast(tuple[int, int], pad_width)] * x.ndim
    else:
        pad_width_seq = cast(list[tuple[int, int]], list(pad_width))

    slices: list[slice] = []
    newshape: list[int] = []
    for ax, w_tpl in enumerate(pad_width_seq):
        if len(w_tpl) != 2:
            msg = f"expect a 2-tuple (before, after), got {w_tpl}."
            raise ValueError(msg)

        sh = eager_shape(x)[ax]

        if w_tpl[0] == 0 and w_tpl[1] == 0:
            sl = slice(None, None, None)
        else:
            stop: int | None
            start, stop = w_tpl
            stop = None if stop == 0 else -stop

            sl = slice(start, stop, None)
            sh += w_tpl[0] + w_tpl[1]

        newshape.append(sh)
        slices.append(sl)

    padded = xp.full(
        tuple(newshape),
        fill_value=constant_values,
        dtype=x.dtype,
        device=_compat.device(x),
    )
    return at(padded, tuple(slices)).set(x)