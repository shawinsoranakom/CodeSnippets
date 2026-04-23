def _max_pool_with_offsets(
    x,
    kernel_size,
    stride,
    padding,
    dilation,
    ceil_mode,
    *,
    n_dim,
):
    x.realize_hint()
    batch = x.shape[:-n_dim]
    dhw = x.shape[-n_dim:]

    dhw_out, ceil_mode = zip(
        *[
            pooling_size(
                dhw[d], d, kernel_size, stride, padding, ceil_mode, dilation=dilation
            )
            for d in range(n_dim)
        ]
    )

    dtype = x.dtype
    min_value = (
        False
        if dtype is torch.bool
        else (float("-inf") if dtype.is_floating_point else torch.iinfo(dtype).min)
    )

    new_size = list(batch) + list(dhw_out)
    if any(padding) or any(ceil_mode) or any(d > 1 for d in dilation):
        x_loader = constant_boundary_condition(x, min_value, dim=n_dim)
    else:
        x_loader = x.make_loader()

    def fn_inner(idx, reduction_idx):
        prefix = idx[:-n_dim]
        bh = idx[-n_dim:]
        ih = [
            (bh[i] * stride[i]) + (reduction_idx[i] * dilation[i]) - padding[i]
            for i in range(n_dim)
        ]
        return x_loader([*prefix, *ih])

    result = Reduction.create(
        reduction_type="max",
        input_node=x,
        device=x.get_device(),
        dst_dtype=dtype,
        src_dtype=dtype,
        inner_fn=fn_inner,
        ranges=new_size,
        reduction_ranges=kernel_size,
    )
    offsets = Reduction.create(
        reduction_type="argmax",
        input_node=x,
        device=x.get_device(),
        dst_dtype=torch.int64,
        src_dtype=dtype,
        inner_fn=fn_inner,
        ranges=new_size,
        reduction_ranges=kernel_size,
    )
    if isinstance(result.data.data, Reduction):  # type: ignore[attr-defined, union-attr]
        # Only realize if reduction isn't unrolled
        result.realize()
    if isinstance(offsets.data.data, Reduction):  # type: ignore[attr-defined, union-attr]
        # Only realize if reduction isn't unrolled
        offsets.realize()

    return result, offsets