def _make_reduction_inner(
    x, *, axis, keepdims, dtype, override_return_dtype, reduction_type=None
):
    if dtype is not None:
        x = to_dtype(x, dtype)
    size = x.get_size()
    axis = OrderedSet[int](_validate_reduction_axis(x, axis))

    kept_sizes = []
    kept_idx = []
    reduced_sizes = []
    reduced_idx = []
    for i in range(len(size)):
        if i in axis:
            reduced_idx.append(i)
            reduced_sizes.append(size[i])
        else:
            kept_idx.append(i)
            kept_sizes.append(size[i])

    # For argmax/argmin compute logical indices when the tensor has non-contiguous layout.
    should_compute_logical_index = False
    if (
        reduction_type in ("argmax", "argmin")
        and len(reduced_sizes) > 1
        and is_triton(x)
    ):
        if isinstance(x.data, PermuteView):
            should_compute_logical_index = True
        elif isinstance(x.data, ir.ReinterpretView) or (
            isinstance(x.data, ir.StorageBox) and isinstance(x.data.data, ir.Buffer)
        ):
            layout = x.get_layout()
            should_compute_logical_index = (
                layout.is_transposed() or not layout.is_contiguous()
            )

    def loader(index, reduction_index):
        assert len(reduction_index) == len(reduced_idx)
        if keepdims:
            assert len(index) == len(size)
            index = [index[i] for i in kept_idx]
        assert len(index) == len(kept_idx)
        new_index = [None] * (len(index) + len(reduction_index))
        for idx, var in itertools.chain(
            zip(kept_idx, index), zip(reduced_idx, reduction_index)
        ):
            new_index[idx] = var
        value = inner_loader(new_index)

        # For argmax/argmin, return tuple with logical linear index if needed
        if should_compute_logical_index:
            rindex = [sympy.expand(i) for i in reduction_index]

            # Compute linear index in row-major order
            # For reduction_ranges = [4, 6]: linear_index = r0 * 6 + r1
            linear_idx = rindex[0]
            for i in range(1, len(rindex)):
                linear_idx = linear_idx * reduced_sizes[i] + rindex[i]

            return (value, ops.index_expr(linear_idx, torch.int64))

        return value

    if keepdims:
        new_size = list(size)
        for i in reduced_idx:
            new_size[i] = sympy.S.One
    else:
        new_size = kept_sizes

    inner_loader = x.make_loader()
    return dict(
        device=x.get_device(),
        dst_dtype=override_return_dtype or x.get_dtype(),
        src_dtype=x.get_dtype(),
        inner_fn=loader,
        ranges=new_size,
        reduction_ranges=reduced_sizes,
    )