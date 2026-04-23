def np_conv3d_transpose(
    x,
    kernel_weights,
    bias_weights,
    strides,
    padding,
    output_padding,
    data_format,
    dilation_rate,
):
    if data_format == "channels_first":
        x = x.transpose((0, 2, 3, 4, 1))
    if isinstance(strides, (tuple, list)):
        h_stride, w_stride, d_stride = strides
    else:
        h_stride = strides
        w_stride = strides
        d_stride = strides
    if isinstance(dilation_rate, (tuple, list)):
        h_dilation, w_dilation, d_dilation = dilation_rate
    else:
        h_dilation = dilation_rate
        w_dilation = dilation_rate
        d_dilation = dilation_rate

    h_kernel, w_kernel, d_kernel, ch_out, ch_in = kernel_weights.shape
    n_batch, h_x, w_x, d_x, _ = x.shape
    # Get output shape and padding
    _, h_out, w_out, d_out, _ = compute_conv_transpose_output_shape(
        x.shape,
        kernel_weights.shape,
        ch_out,
        strides,
        padding,
        output_padding,
        data_format,
        dilation_rate,
    )
    jax_padding = compute_conv_transpose_padding_args_for_jax(
        input_shape=x.shape,
        kernel_shape=kernel_weights.shape,
        strides=strides,
        padding=padding,
        output_padding=output_padding,
        dilation_rate=dilation_rate,
    )
    h_pad_side1 = h_kernel - 1 - jax_padding[0][0]
    w_pad_side1 = w_kernel - 1 - jax_padding[1][0]
    d_pad_side1 = d_kernel - 1 - jax_padding[2][0]

    if h_dilation > 1 or w_dilation > 1 or d_dilation > 1:
        # Increase kernel size
        new_h_kernel = h_kernel + (h_dilation - 1) * (h_kernel - 1)
        new_w_kernel = w_kernel + (w_dilation - 1) * (w_kernel - 1)
        new_d_kernel = d_kernel + (d_dilation - 1) * (d_kernel - 1)
        new_kernel_size_tuple = (new_h_kernel, new_w_kernel, new_d_kernel)
        new_kernel_weights = np.zeros(
            (*new_kernel_size_tuple, ch_out, ch_in),
            dtype=kernel_weights.dtype,
        )
        new_kernel_weights[::h_dilation, ::w_dilation, ::d_dilation] = (
            kernel_weights
        )
        kernel_weights = new_kernel_weights
        h_kernel, w_kernel, d_kernel = kernel_weights.shape[:3]

    # Compute output
    output = np.zeros(
        [
            n_batch,
            h_out + h_kernel,
            w_out + w_kernel,
            d_out + d_kernel,
            ch_out,
        ]
    )
    for nb in range(n_batch):
        for h_x_idx in range(h_x):
            h_out_idx = h_x_idx * h_stride  # Index in output
            for w_x_idx in range(w_x):
                w_out_idx = w_x_idx * w_stride
                for d_x_idx in range(d_x):
                    d_out_idx = d_x_idx * d_stride
                    output[
                        nb,
                        h_out_idx : h_out_idx + h_kernel,
                        w_out_idx : w_out_idx + w_kernel,
                        d_out_idx : d_out_idx + d_kernel,
                        :,
                    ] += np.sum(
                        kernel_weights[:, :, :, :, :]
                        * x[nb, h_x_idx, w_x_idx, d_x_idx, :],
                        axis=-1,
                    )
    output = output + bias_weights

    # Cut padding results from output
    output = output[
        :,
        h_pad_side1 : h_out + h_pad_side1,
        w_pad_side1 : w_out + w_pad_side1,
        d_pad_side1 : d_out + d_pad_side1,
    ]
    if data_format == "channels_first":
        output = output.transpose((0, 4, 1, 2, 3))
    return output