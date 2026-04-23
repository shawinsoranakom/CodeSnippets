def adaptive_max_pool2d(x, output_size):
    if x.get_dtype() == torch.int64:
        # not supported in eager
        raise RuntimeError("adaptive_max_pool2d not implemented for Long")
    assert isinstance(x, TensorBox)
    assert len(output_size) == 2
    x.realize_hint()

    *batch, h_in, w_in = x.get_size()

    h_in = V.graph.sizevars.guard_int(h_in)
    w_in = V.graph.sizevars.guard_int(w_in)

    h_out, w_out = output_size

    if h_out == 0 or w_out == 0:
        o_size = [*batch, h_out, w_out]
        return empty(o_size, dtype=x.get_dtype(), device=x.get_device()), empty(
            o_size, dtype=torch.int64, device=x.get_device()
        )

    if h_in % h_out == 0 and w_in % w_out == 0:
        # This is handled by a decomposition
        raise ValueError

    h_kernel_max = ceildiv((h_in + h_out - 1), h_out)
    w_kernel_max = ceildiv((w_in + w_out - 1), w_out)

    new_size = list(batch) + [h_out, w_out]
    dtype = x.get_dtype()

    window_size = h_kernel_max * w_kernel_max
    if window_size > 25:
        # Kernel size too big. Results in hard-to-optimize Triton code. Use fallback.
        return fallback_adaptive_max_pool2d(x, output_size)

    def start_index(index, out_dim, inp_dim):
        return FloorDiv((index * inp_dim), out_dim)

    def end_index(index, out_dim, inp_dim):
        return FloorDiv((index + 1) * inp_dim + out_dim - 1, out_dim)

    inner_func_max_val = _adaptive_pooling_fn(
        start_index=start_index,
        end_index=end_index,
        kernel_maxes=[h_kernel_max, w_kernel_max],
        in_sizes=[h_in, w_in],
        out_sizes=[h_out, w_out],
        pooling_fn=ops.maximum,
    )

    inner_func_max_idx = _adaptive_pooling_fn_with_idx(
        start_index=start_index,
        end_index=end_index,
        kernel_maxes=[h_kernel_max, w_kernel_max],
        in_sizes=[h_in, w_in],
        out_sizes=[h_out, w_out],
        pooling_fn=ops.maximum,
    )

    def inner_fn_max_val(idx):
        return inner_func_max_val(idx, pad_adaptive_loader(x, float("-inf")))

    def inner_fn_max_idx(idx):
        return inner_func_max_idx(idx, pad_adaptive_loader(x, float("-inf")))

    rv = Pointwise.create(
        device=x.get_device(),
        dtype=dtype,
        inner_fn=inner_fn_max_val,
        ranges=new_size,
    )
    ri = Pointwise.create(
        device=x.get_device(),
        dtype=torch.int64,
        inner_fn=inner_fn_max_idx,
        ranges=new_size,
    )
    return rv, ri