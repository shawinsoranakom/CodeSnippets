def _pad_as_cat(
    x: TensorBox, padding: Sequence[int], fill_value: float
) -> TensorBox | None:
    """Decompose right-pad into cat([x, fill], dim) and delegate to cat lowering.

    The cat lowering already has heuristics for choosing between pointwise_cat
    (fusion) and ConcatKernel (memory planning / zero-copy).  By routing through
    cat() we reuse those heuristics rather than duplicating them here.
    """
    # Bail out for symbolic padding, dynamic shapes
    if not all(isinstance(p, int) for p in padding):
        return None

    sizes = x.get_size()
    ndim = len(sizes)
    pad_pairs = list(zip(padding[::2], padding[1::2]))

    # Only support single-dimension right-pad
    pad_dim = None
    pad_amount = None
    for i, (left, right) in enumerate(pad_pairs):
        if left != 0:
            return None
        if right > 0:
            if pad_dim is not None:
                return None  # multi-dim pad
            pad_dim = ndim - 1 - i  # padding format is reversed dim order
            pad_amount = right
        elif right < 0:
            return None  # trim, not pad

    if pad_dim is None:
        return None

    # CPU cat always uses ConcatKernel (no pointwise_cat), which adds
    # extra kernel launches for the fill.  Skip pad-as-cat on CPU.
    device = x.get_device()
    if device is not None and device.type == "cpu":
        return None

    # Build the fill tensor for the padding region
    pad_shape = list(sizes)
    pad_shape[pad_dim] = pad_amount
    dtype = x.get_dtype()
    fill_value_typed = dtype_to_type(dtype)(fill_value)
    pad_tensor = tensor_constructor(fill_value_typed)(
        pad_shape, dtype=dtype, device=device
    )

    counters["inductor"]["pad_rewritten_as_cat"] += 1
    return cat([x, pad_tensor], pad_dim)