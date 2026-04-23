def max_pool2d_with_indices_backward(
    grad_output, x, kernel_size, stride, padding, dilation, ceil_mode, indices
):
    if padding == 0:
        padding = [0, 0]
    if dilation == 1:
        dilation = [1, 1]
    if not stride:
        stride = kernel_size

    assert isinstance(x, TensorBox)
    assert len(kernel_size) == 2
    assert len(stride) == 2
    assert len(padding) == 2
    assert len(dilation) == 2
    assert len(x.get_size()) in (3, 4)

    # we will read this many times, so make sure it is computed
    grad_output.realize_hint()
    gO_stride = grad_output.maybe_get_stride()
    x_stride: Sequence[Any] | None
    if isinstance(x, TensorBox) and isinstance(x.data.data, Pointwise):  # type: ignore[attr-defined]
        data = x.data.data  # type: ignore[attr-defined]
        device = data.get_device()
        assert device is not None
        x_buffer = ir.ComputedBuffer(
            name=None,
            layout=ir.FlexibleLayout(
                device=device,
                dtype=data.get_dtype(),
                size=data.get_size(),
            ),
            data=data,
        )
        x_buffer.decide_layout()
        x_stride = x_buffer.get_stride()
    else:
        x_stride = x.maybe_get_stride()

    is_channels_last = (x_stride is not None and x_stride[1] == 1) or (
        gO_stride is not None and gO_stride[1] == 1
    )
    if any(d != 1 for d in dilation):
        # dilation NYI
        return fallback_max_pool2d_with_indices_backward(
            grad_output, x, kernel_size, stride, padding, dilation, ceil_mode, indices
        )

    *_batch, _height, width = x.get_size()
    *_, pooled_height, pooled_width = grad_output.get_size()

    indices_loader = indices.make_loader()
    grad_loader = grad_output.make_loader()
    new_size = list(x.get_size())

    h_window_size = max(
        max(FloorDiv(h, stride[0]) - max(0, FloorDiv(h - kernel_size[0], stride[0])), 1)
        for h in range(kernel_size[0] * 2)
    )
    w_window_size = max(
        max(FloorDiv(w, stride[1]) - max(0, FloorDiv(w - kernel_size[1], stride[1])), 1)
        for w in range(kernel_size[1] * 2)
    )

    window_size = h_window_size * w_window_size

    if window_size > 25:
        # Kernel size too big. Results in hard-to-optimize Triton code. Use fallback.
        return fallback_max_pool2d_with_indices_backward(
            grad_output, x, kernel_size, stride, padding, dilation, ceil_mode, indices
        )

    indices_size = indices.get_size()

    def fn(idx):
        *prefix, h, w = idx
        index_test = ops.index_expr(h * width + w, torch.int32)
        h = h + padding[0]
        w = w + padding[1]
        phstart = ops.index_expr(
            FloorDiv(h - kernel_size[0] + stride[0], stride[0]), torch.int32
        )
        pwstart = ops.index_expr(
            FloorDiv(w - kernel_size[1] + stride[1], stride[1]), torch.int32
        )
        phend = ops.index_expr(FloorDiv(h, stride[0]) + 1, torch.int32)
        pwend = ops.index_expr(FloorDiv(w, stride[1]) + 1, torch.int32)

        phstart = ops.maximum(phstart, ops.constant(0, torch.int32))
        pwstart = ops.maximum(pwstart, ops.constant(0, torch.int32))
        phend = ops.minimum(phend, ops.index_expr(pooled_height, torch.int32))
        pwend = ops.minimum(pwend, ops.index_expr(pooled_width, torch.int32))

        gradient = None
        for ph_ in range(h_window_size):
            for pw_ in range(w_window_size):
                ph = ops.add(phstart, ops.constant(ph_, torch.int32))
                pw = ops.add(pwstart, ops.constant(pw_, torch.int32))
                grad_index = [
                    *prefix,
                    ops.indirect_indexing(
                        ops.minimum(ph, ops.sub(phend, ops.constant(1, torch.int32))),
                        indices_size[-2],
                        check=False,
                    ),
                    ops.indirect_indexing(
                        ops.minimum(pw, ops.sub(pwend, ops.constant(1, torch.int32))),
                        indices_size[-1],
                        check=False,
                    ),
                ]

                index_actual = indices_loader(grad_index)
                grad_part = grad_loader(grad_index)
                check = ops.eq(index_actual, index_test)

                if gradient is None:
                    # don't need mask for 0, 0
                    gradient = ops.where(
                        check, grad_part, ops.constant(0.0, torch.float32)
                    )
                else:
                    mask = ops.and_(
                        ops.and_(
                            ops.lt(ph, phend),
                            ops.lt(pw, pwend),
                        ),
                        check,
                    )
                    gradient = ops.where(mask, ops.add(gradient, grad_part), gradient)
        assert gradient is not None
        return gradient

    out = Pointwise.create(
        device=grad_output.get_device(),
        dtype=grad_output.get_dtype(),
        inner_fn=fn,
        ranges=new_size,
    )
    if is_channels_last:
        return ir.ExternKernel.require_channels_last(out)
    else:
        return out