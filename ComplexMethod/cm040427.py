def fold(x, output_size, kernel_size, dilation=1, padding=0, stride=1):
    """TensorFlow implementation of Fold (col2im).
    Combine an array of sliding local blocks into a large tensor.

    Args:
        x: 3-D tensor, shape (N, C*kH*kW, L)  **required**.
        output_size: int or (oH, oW)
        kernel_size: int or (kH, kW)
        dilation: int or (dH, dW), default 1
        padding: int or (pH, pW), default 0
        stride: int or (sH, sW), default 1

    Returns:
        4-D tensor, shape (N, C, oH, oW)
    """
    k = (
        (kernel_size, kernel_size)
        if isinstance(kernel_size, int)
        else kernel_size
    )
    o = (
        (output_size, output_size)
        if isinstance(output_size, int)
        else output_size
    )
    d = (dilation, dilation) if isinstance(dilation, int) else dilation
    p = (padding, padding) if isinstance(padding, int) else padding
    s = (stride, stride) if isinstance(stride, int) else stride

    N = tf.shape(x)[0]
    CKK = x.shape[1]
    kH, kW = k
    oH, oW = o
    C = CKK // (kH * kW)

    # Number of output patches along each dimension
    nH = (oH + 2 * p[0] - d[0] * (kH - 1) - 1) // s[0] + 1
    nW = (oW + 2 * p[1] - d[1] * (kW - 1) - 1) // s[1] + 1

    # Reshape: (N, C*kH*kW, L) -> (N, C, kH, kW, nH, nW)
    x = tf.reshape(x, [N, C, kH, kW, nH, nW])

    # Padded output size
    oH_pad = oH + 2 * p[0]
    oW_pad = oW + 2 * p[1]

    # Build scatter indices for all kernel positions
    # Process one sample at a time using vectorized_map
    def _fold_single(x_single):
        # x_single: (C, kH, kW, nH, nW)
        output = tf.zeros([C, oH_pad, oW_pad], dtype=x.dtype)
        for i in range(kH):
            for j in range(kW):
                h_start = i * d[0]
                w_start = j * d[1]
                h_indices = tf.range(nH) * s[0] + h_start
                w_indices = tf.range(nW) * s[1] + w_start
                # x_single[:, i, j, :, :] has shape (C, nH, nW)
                patch = x_single[:, i, j, :, :]
                # Build indices for scatter
                c_idx = tf.repeat(tf.range(C), nH * nW)  # (C*nH*nW,)
                h_idx = tf.tile(tf.repeat(h_indices, nW), [C])  # (C*nH*nW,)
                w_idx = tf.tile(tf.tile(w_indices, [nH]), [C])  # (C*nH*nW,)
                indices = tf.stack(
                    [c_idx, h_idx, w_idx], axis=1
                )  # (C*nH*nW, 3)
                values = tf.reshape(patch, [-1])  # (C*nH*nW,)
                output = tf.tensor_scatter_nd_add(output, indices, values)
        return output

    output = tf.vectorized_map(_fold_single, x)  # (N, C, oH_pad, oW_pad)

    # Remove padding
    if p[0] > 0 or p[1] > 0:
        output = output[:, :, p[0] : oH_pad - p[0], p[1] : oW_pad - p[1]]

    return output