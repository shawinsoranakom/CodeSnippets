def avg_pool3d_backward(
    grad_output,
    x,
    kernel_size,
    stride,
    padding,
    ceil_mode,
    count_include_pad,
    divisor_override=None,
):
    assert divisor_override is None or divisor_override != 0, "divisor must be not zero"
    if not stride:
        stride = kernel_size
    if not padding:
        padding = [0, 0, 0]

    assert isinstance(grad_output, TensorBox)
    assert isinstance(x, TensorBox)
    assert len(kernel_size) == 3
    assert len(stride) == 3
    assert len(padding) == 3
    assert len(x.get_size()) in (4, 5)

    grad_output.realize_hint()

    *_batch, depth, height, width = x.get_size()

    _d_out, ceil_mode_d = pooling_size(
        depth, 0, kernel_size, stride, padding, ceil_mode
    )
    _h_out, ceil_mode_h = pooling_size(
        height, 1, kernel_size, stride, padding, ceil_mode
    )
    _w_out, ceil_mode_w = pooling_size(
        width, 2, kernel_size, stride, padding, ceil_mode
    )

    grad_loader = grad_output.make_loader()
    had_padding = any(padding) or ceil_mode_d or ceil_mode_h or ceil_mode_w

    *_, pooled_depth, pooled_height, pooled_width = grad_output.get_size()
    new_size = list(x.get_size())
    dtype = x.get_dtype()

    d_window_size, h_window_size, w_window_size = (
        max(
            max(d // stride[i] - max(0, (d - kernel_size[i]) // stride[i]), 1)
            for d in range(kernel_size[i] * 2)
        )
        for i in range(3)
    )

    window_size = d_window_size * h_window_size * w_window_size
    if window_size > 125:
        # Kernel size too big. Results in hard-to-optimize Triton code.
        return fallback_avg_pool3d_backward(
            grad_output,
            x,
            kernel_size,
            stride,
            padding,
            ceil_mode,
            count_include_pad,
            divisor_override,
        )

    def compute_pool_size_without_padding(pd, ph, pw):
        stride_d, stride_h, stride_w = (ops.constant(s, torch.int32) for s in stride)
        pad_d, pad_h, pad_w = (ops.constant(p, torch.int32) for p in padding)
        kernel_d, kernel_h, kernel_w = (
            ops.constant(k, torch.int32) for k in kernel_size
        )

        dstart, hstart, wstart = (
            ops.sub(ops.mul(p, s), pad)
            for p, s, pad in zip(
                [pd, ph, pw], [stride_d, stride_h, stride_w], [pad_d, pad_h, pad_w]
            )
        )
        dend, hend, wend = (
            ops.minimum(
                ops.add(start, k), ops.add(ops.index_expr(dim, torch.int32), pad)
            )
            for start, k, dim, pad in zip(
                [dstart, hstart, wstart],
                [kernel_d, kernel_h, kernel_w],
                [depth, height, width],
                [pad_d, pad_h, pad_w],
            )
        )
        dstart, hstart, wstart = (
            ops.maximum(start, ops.constant(0, torch.int32))
            for start in [dstart, hstart, wstart]
        )
        dend, hend, wend = (
            ops.minimum(end, ops.index_expr(dim, torch.int32))
            for end, dim in zip([dend, hend, wend], [depth, height, width])
        )
        divide_factor = ops.mul(
            ops.mul(ops.sub(dend, dstart), ops.sub(hend, hstart)), ops.sub(wend, wstart)
        )
        return divide_factor

    def fn(idx):
        *prefix, d, h, w = idx
        d, h, w = (v + pad for v, pad in zip([d, h, w], padding))

        pdstart, phstart, pwstart = (
            ops.index_expr(FloorDiv(v - k + s, s), torch.int32)
            for v, k, s in zip([d, h, w], kernel_size, stride)
        )

        pdend, phend, pwend = (
            ops.index_expr(FloorDiv(v, s) + 1, torch.int32)
            for v, s in zip([d, h, w], stride)
        )

        pdstart, phstart, pwstart = (
            ops.maximum(pstart, ops.constant(0, torch.int32))
            for pstart in [pdstart, phstart, pwstart]
        )
        pdend, phend, pwend = (
            ops.minimum(pend, ops.index_expr(pooled_dim, torch.int32))
            for pend, pooled_dim in zip(
                [pdend, phend, pwend], [pooled_depth, pooled_height, pooled_width]
            )
        )

        gradient = None
        # Iterate over the 3D region to accumulate gradients
        for pd_ in range(d_window_size):
            for ph_ in range(h_window_size):
                for pw_ in range(w_window_size):
                    pd, ph, pw = (
                        ops.add(pstart, ops.constant(p_, torch.int32))
                        for pstart, p_ in zip(
                            [pdstart, phstart, pwstart], [pd_, ph_, pw_]
                        )
                    )

                    if divisor_override is not None:
                        scale = divisor_override
                    elif count_include_pad or not had_padding:
                        scale = kernel_size[0] * kernel_size[1] * kernel_size[2]
                    else:
                        scale = compute_pool_size_without_padding(pd, ph, pw)

                    part = ops.truediv(
                        grad_loader(
                            [
                                *prefix,
                                ops.indirect_indexing(
                                    ops.minimum(
                                        pd, ops.sub(pdend, ops.constant(1, torch.int32))
                                    ),
                                    pooled_depth,
                                    check=False,
                                ),
                                ops.indirect_indexing(
                                    ops.minimum(
                                        ph, ops.sub(phend, ops.constant(1, torch.int32))
                                    ),
                                    pooled_height,
                                    check=False,
                                ),
                                ops.indirect_indexing(
                                    ops.minimum(
                                        pw, ops.sub(pwend, ops.constant(1, torch.int32))
                                    ),
                                    pooled_width,
                                    check=False,
                                ),
                            ]
                        ),
                        scale,
                    )

                    mask = ops.and_(
                        ops.and_(ops.lt(pd, pdend), ops.lt(ph, phend)),
                        ops.lt(pw, pwend),
                    )
                    if gradient is None:
                        gradient = ops.where(
                            mask, part, ops.constant(0.0, torch.float32)
                        )
                    else:
                        gradient = ops.where(mask, ops.add(gradient, part), gradient)
        assert gradient is not None
        return gradient

    rv = Pointwise.create(
        device=grad_output.get_device(),
        dtype=dtype,
        inner_fn=fn,
        ranges=new_size,
    )
    return rv