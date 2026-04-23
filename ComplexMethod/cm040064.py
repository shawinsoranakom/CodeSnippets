def np_depthwise_conv2d(
    x,
    kernel_weights,
    bias_weights,
    strides,
    padding,
    data_format,
    dilation_rate,
):
    if data_format == "channels_first":
        x = x.transpose((0, 2, 3, 1))
    if isinstance(strides, (tuple, list)):
        h_stride, w_stride = strides
    else:
        h_stride = strides
        w_stride = strides
    if isinstance(dilation_rate, (tuple, list)):
        h_dilation, w_dilation = dilation_rate
    else:
        h_dilation = dilation_rate
        w_dilation = dilation_rate
    h_kernel, w_kernel, ch_in, ch_out = kernel_weights.shape

    if h_dilation > 1 or w_dilation > 1:
        new_h_kernel = h_kernel + (h_dilation - 1) * (h_kernel - 1)
        new_w_kernel = w_kernel + (w_dilation - 1) * (w_kernel - 1)
        new_kenel_size_tuple = (new_h_kernel, new_w_kernel)
        new_kernel_weights = np.zeros(
            (*new_kenel_size_tuple, ch_in, ch_out),
            dtype=kernel_weights.dtype,
        )
        new_kernel_weights[::h_dilation, ::w_dilation] = kernel_weights
        kernel_weights = new_kernel_weights
        h_kernel, w_kernel = kernel_weights.shape[:2]

    if padding == "same":
        n_batch, h_x, w_x, _ = x.shape
        h_pad = _same_padding(h_x, h_kernel, h_stride)
        w_pad = _same_padding(w_x, w_kernel, w_stride)
        npad = [(0, 0)] * x.ndim
        npad[1] = h_pad
        npad[2] = w_pad
        x = np.pad(x, pad_width=npad, mode="constant", constant_values=0)

    n_batch, h_x, w_x, _ = x.shape
    h_out = int((h_x - h_kernel) / h_stride) + 1
    w_out = int((w_x - w_kernel) / w_stride) + 1

    out_grps = []
    bias_weights = bias_weights.reshape(ch_in, ch_out)
    for ch_in_idx in range(ch_in):
        for ch_out_idx in range(ch_out):
            x_in = np.ascontiguousarray(x[..., ch_in_idx])
            stride_shape = (n_batch, h_out, w_out, h_kernel, w_kernel)
            strides = (
                x_in.strides[0],
                h_stride * x_in.strides[1],
                w_stride * x_in.strides[2],
                x_in.strides[1],
                x_in.strides[2],
            )
            inner_dim = h_kernel * w_kernel
            x_strided = as_strided(
                x_in, shape=stride_shape, strides=strides
            ).reshape(-1, inner_dim)
            kernel_weights_grp = kernel_weights[
                ..., ch_in_idx, ch_out_idx
            ].reshape(-1, 1)
            bias_weights_grp = bias_weights[..., ch_in_idx, ch_out_idx]
            out_grps.append(
                (x_strided @ kernel_weights_grp + bias_weights_grp).reshape(
                    n_batch, h_out, w_out, 1
                )
            )
    out = np.concatenate(out_grps, axis=-1)
    if data_format == "channels_first":
        out = out.transpose((0, 3, 1, 2))
    return out