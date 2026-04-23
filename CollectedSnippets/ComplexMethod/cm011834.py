def resize(x, size, *, memory_format=None):
    assert isinstance(x, TensorBox)
    assert isinstance(size, (list, tuple))

    if memory_format is None:
        memory_format = torch.contiguous_format
    if memory_format == torch.preserve_format:
        raise RuntimeError(f"unsupported memory format: {memory_format}")

    if memory_format == torch.channels_last:
        assert len(size) == 4
    if memory_format == torch.channels_last_3d:
        assert len(size) == 5

    old_numel = x.get_numel()
    dtype = x.get_dtype()
    device = x.get_device_or_error()

    if (
        torch.are_deterministic_algorithms_enabled()
        and torch.utils.deterministic.fill_uninitialized_memory  # type: ignore[attr-defined]
    ):
        if is_float_dtype(dtype):
            uninitialized_val = float("nan")
        elif is_integer_dtype(dtype):
            uninitialized_val = torch.iinfo(dtype).max
        else:
            uninitialized_val = True
    else:
        # using zero as that is what empty does
        uninitialized_val = 0.0

    if V.graph.sizevars.statically_known_equals(old_numel, 0):  # type: ignore[arg-type]
        return full(size, uninitialized_val, dtype=dtype, device=device)

    strides = x.maybe_get_stride()
    has_overlapping = strides is not None and any(
        V.graph.sizevars.statically_known_equals(s, 0) for s in strides
    )
    if has_overlapping:
        # overlapping: provide a contiguous logical view
        x_flat = view(x, [old_numel])
    else:
        # non-overlapping: keep storage order
        if isinstance(x.data, ir.BaseView):
            x.data = x.data.unwrap_view()
        x_flat = as_strided(x, [old_numel], [1])
    flat_loader = x_flat.make_loader()
    out_stride = ir.FlexibleLayout.stride_ordered_for_memory_format(size, memory_format)
    out_indexer = ir.FixedLayout(device, dtype, size, out_stride).make_indexer()

    def inner_fn(idx):
        flat_index = out_indexer(idx)
        flat_index_expr = ops.index_expr(flat_index, torch.int64)
        limit = ops.index_expr(old_numel, torch.int64)
        mask = ops.lt(flat_index_expr, limit)
        return ops.masked(mask, lambda: flat_loader([flat_index]), uninitialized_val)

    out = Pointwise.create(
        device=device, dtype=dtype, inner_fn=inner_fn, ranges=list(size)
    )
    return out