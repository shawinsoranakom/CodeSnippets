def np_conv1d(
    x,
    kernel_weights,
    bias_weights,
    strides,
    padding,
    data_format,
    dilation_rate,
    groups,
):
    if data_format == "channels_first":
        x = x.swapaxes(1, 2)
    if isinstance(strides, (tuple, list)):
        h_stride = strides[0]
    else:
        h_stride = strides
    if isinstance(dilation_rate, (tuple, list)):
        dilation_rate = dilation_rate[0]
    kernel_size, ch_in, ch_out = kernel_weights.shape

    if dilation_rate > 1:
        new_kernel_size = kernel_size + (dilation_rate - 1) * (kernel_size - 1)
        new_kernel_weights = np.zeros(
            (new_kernel_size, ch_in, ch_out), dtype=kernel_weights.dtype
        )
        new_kernel_weights[::dilation_rate] = kernel_weights
        kernel_weights = new_kernel_weights
        kernel_size = kernel_weights.shape[0]

    if padding != "valid":
        n_batch, h_x, _ = x.shape
        h_pad = _same_padding(h_x, kernel_size, h_stride)
        npad = [(0, 0)] * x.ndim
        if padding == "causal":
            npad[1] = (h_pad[0] + h_pad[1], 0)
        else:
            npad[1] = h_pad
        x = np.pad(x, pad_width=npad, mode="constant", constant_values=0)

    n_batch, h_x, _ = x.shape
    h_out = int((h_x - kernel_size) / h_stride) + 1

    kernel_weights = kernel_weights.reshape(-1, ch_out)
    bias_weights = bias_weights.reshape(1, ch_out)

    out_grps = []
    for grp in range(1, groups + 1):
        x_in = x[..., (grp - 1) * ch_in : grp * ch_in]
        stride_shape = (n_batch, h_out, kernel_size, ch_in)
        strides = (
            x_in.strides[0],
            h_stride * x_in.strides[1],
            x_in.strides[1],
            x_in.strides[2],
        )
        inner_dim = kernel_size * ch_in
        x_strided = as_strided(
            x_in, shape=stride_shape, strides=strides
        ).reshape(n_batch, h_out, inner_dim)
        ch_out_groups = ch_out // groups
        kernel_weights_grp = kernel_weights[
            ..., (grp - 1) * ch_out_groups : grp * ch_out_groups
        ]
        bias_weights_grp = bias_weights[
            ..., (grp - 1) * ch_out_groups : grp * ch_out_groups
        ]
        out_grps.append(x_strided @ kernel_weights_grp + bias_weights_grp)
    out = np.concatenate(out_grps, axis=-1)
    if data_format == "channels_first":
        out = out.swapaxes(1, 2)
    return out