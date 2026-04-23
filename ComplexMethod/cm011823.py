def _avg_poolnd(
    x,
    kernel_size,
    stride,
    padding,
    ceil_mode,
    count_include_pad,
    divisor_override,
    dim,
):
    if not stride:
        stride = kernel_size
    if not padding:
        padding = [0] * dim
    kernel_size = pad_listlike(kernel_size, dim)
    stride = pad_listlike(stride, dim)
    padding = pad_listlike(padding, dim)

    assert isinstance(x, TensorBox)
    assert len(kernel_size) == dim
    assert len(stride) == dim
    assert len(padding) == dim
    assert len(x.get_size()) in (dim + 1, dim + 2)

    x.realize_hint()
    batch = x.get_size()[:-dim]
    h = x.get_size()[-dim:]

    h_out, ceil_modes = zip(
        *[
            pooling_size(h[i], i, kernel_size, stride, padding, ceil_mode)
            for i in range(dim)
        ]
    )

    if any(padding) or any(ceil_modes):
        x_loader = constant_boundary_condition(x, 0.0, dim=dim)
        had_padding = True
    else:
        x_loader = x.make_loader()
        had_padding = False

    new_size = list(batch) + list(h_out)
    dtype = x.get_dtype()
    # compute in higher-precision until scaling
    output_dtype = get_promoted_dtype(
        x,
        type_promotion_kind=ELEMENTWISE_TYPE_PROMOTION_KIND.DEFAULT,
        return_compute_dtype=True,
    )

    def fn_inner(idx, reduction_idx):
        prefix = idx[:-dim]
        bh = idx[-dim:]
        ih = reduction_idx
        ih = [bh[i] * stride[i] + ih[i] - padding[i] for i in range(dim)]
        return x_loader([*prefix, *ih])

    window_size = functools.reduce(operator.mul, kernel_size)

    if window_size > 25 and any(
        V.graph.sizevars.statically_known_true(sympy.Ne(k, s))
        for k, s in zip(kernel_size, stride)
    ):
        fallback = fallbacks_avg_poolnd[dim - 1]
        return fallback(
            x,
            kernel_size,
            stride,
            padding,
            ceil_mode,
            count_include_pad,
            divisor_override,
        )

    # TODO: remove this when #100331 is merged. We only do this
    # for window_size <=25 to avoid performance regressions compared
    # to the previous algorithm which unrolled manually for <=25
    context = (
        config.patch(unroll_reductions_threshold=25)
        if window_size <= 25
        else contextlib.nullcontext()
    )

    device = x.get_device()
    assert device is not None

    with context:
        rv = Reduction.create(
            reduction_type="sum",
            input_node=x,
            device=device,
            dst_dtype=output_dtype,
            src_dtype=dtype,
            inner_fn=fn_inner,
            ranges=new_size,
            reduction_ranges=kernel_size,
        )
    if hasattr(rv.data, "data") and isinstance(rv.data.data, Reduction):
        # Only realize if reduction isn't unrolled
        rv.realize()

    if not had_padding or divisor_override:
        divisor = divisor_override if divisor_override else window_size
        result = div_prim(rv, divisor)
    else:

        def fn_count(idx):
            bh = idx[-dim:]

            divide_factors = []
            for i in range(dim):
                hstart = bh[i] * stride[i] - padding[i]
                hend = sympy.Min(hstart + kernel_size[i], h[i] + padding[i])
                if not count_include_pad:
                    hstart = sympy.Max(hstart, 0)
                    hend = sympy.Min(hend, h[i])
                factor = ops.index_expr(hend - hstart, torch.int32)
                divide_factors.append(factor)
            return functools.reduce(ops.mul, divide_factors)

        divide_factor = Pointwise.create(
            device=x.get_device(),
            dtype=dtype,
            inner_fn=fn_count,
            ranges=new_size,
        )
        result = div_prim(rv, divide_factor)

    return to_dtype(result, dtype)