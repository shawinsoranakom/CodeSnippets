def fn(idx):
        *prefix, h, w = idx
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

                if divisor_override is not None:
                    scale = divisor_override
                elif count_include_pad or not had_padding:
                    scale = kernel_size[0] * kernel_size[1]
                else:
                    scale = compute_pool_size_without_padding(ph, pw)

                part = ops.truediv(
                    grad_loader(
                        [
                            *prefix,
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
                    ops.lt(ph, phend),
                    ops.lt(pw, pwend),
                )
                if gradient is None:
                    gradient = ops.where(mask, part, ops.constant(0.0, torch.float32))
                else:
                    gradient = ops.where(mask, ops.add(gradient, part), gradient)
        assert gradient is not None
        return gradient