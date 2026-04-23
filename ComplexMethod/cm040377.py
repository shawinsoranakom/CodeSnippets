def _adaptive_pool3d_impl(inputs, output_size, mode, data_format):
    if isinstance(output_size, int):
        output_size = (output_size, output_size, output_size)

    if data_format == "channels_first":
        inputs = np.transpose(inputs, (0, 2, 3, 4, 1))

    n, d, h, w, c = inputs.shape
    out_d, out_h, out_w = output_size

    small_d, big_d = compute_adaptive_pooling_window_sizes(d, out_d)
    gather_d = _compute_adaptive_pooling_gather_indices(d, out_d, big_d)

    x_d = np.transpose(inputs, (0, 2, 3, 1, 4)).reshape(n * h * w, d, c)

    sv_small_d = _strided_view_1d(x_d, small_d)
    small_pool_d = (
        np.mean(sv_small_d, axis=2)
        if mode == "average"
        else np.max(sv_small_d, axis=2)
    )

    sv_big_d = _strided_view_1d(x_d, big_d)
    big_pool_d = (
        np.mean(sv_big_d, axis=2)
        if mode == "average"
        else np.max(sv_big_d, axis=2)
    )

    combined_d = np.concatenate([small_pool_d, big_pool_d], axis=1)
    pooled_d = combined_d[:, gather_d, :].reshape(n, h, w, out_d, c)
    pooled_d = np.transpose(pooled_d, (0, 3, 1, 2, 4))

    small_h, big_h = compute_adaptive_pooling_window_sizes(h, out_h)
    gather_h = _compute_adaptive_pooling_gather_indices(h, out_h, big_h)

    x_h = np.transpose(pooled_d, (0, 1, 3, 2, 4)).reshape(n * out_d * w, h, c)

    sv_small_h = _strided_view_1d(x_h, small_h)
    small_pool_h = (
        np.mean(sv_small_h, axis=2)
        if mode == "average"
        else np.max(sv_small_h, axis=2)
    )

    sv_big_h = _strided_view_1d(x_h, big_h)
    big_pool_h = (
        np.mean(sv_big_h, axis=2)
        if mode == "average"
        else np.max(sv_big_h, axis=2)
    )

    combined_h = np.concatenate([small_pool_h, big_pool_h], axis=1)
    pooled_h = combined_h[:, gather_h, :].reshape(n, out_d, w, out_h, c)
    pooled_h = np.transpose(pooled_h, (0, 1, 3, 2, 4))

    small_w, big_w = compute_adaptive_pooling_window_sizes(w, out_w)
    gather_w = _compute_adaptive_pooling_gather_indices(w, out_w, big_w)

    x_w = pooled_h.reshape(n * out_d * out_h, w, c)

    sv_small_w = _strided_view_1d(x_w, small_w)
    small_pool_w = (
        np.mean(sv_small_w, axis=2)
        if mode == "average"
        else np.max(sv_small_w, axis=2)
    )

    sv_big_w = _strided_view_1d(x_w, big_w)
    big_pool_w = (
        np.mean(sv_big_w, axis=2)
        if mode == "average"
        else np.max(sv_big_w, axis=2)
    )

    combined_w = np.concatenate([small_pool_w, big_pool_w], axis=1)
    out = combined_w[:, gather_w, :].reshape(n, out_d, out_h, out_w, c)

    if data_format == "channels_first":
        out = np.transpose(out, (0, 4, 1, 2, 3))

    return out