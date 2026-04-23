def correlate(x1, x2, mode="valid"):
    x1 = convert_to_tensor(x1)
    x2 = convert_to_tensor(x2)

    dtype = dtypes.result_type(
        getattr(x1, "dtype", type(x1)),
        getattr(x2, "dtype", type(x2)),
    )
    if dtype == tf.int64:
        dtype = tf.float64
    elif dtype not in [tf.bfloat16, tf.float16, tf.float64]:
        dtype = tf.float32

    x1 = tf.cast(x1, dtype)
    x2 = tf.cast(x2, dtype)

    def _pack(a, b):
        # a: input [N] -> [1,N,1];
        # b: filter [M] -> [M,1,1]
        return (
            tf.reshape(a, (1, shape_op(a)[0], 1)),
            tf.reshape(b, (shape_op(b)[0], 1, 1)),
        )

    def _full_corr(x1, x2):
        """Compute 'full' correlation result (length = n + m - 1)."""
        m = shape_op(x2)[0]
        pad = (
            builtins.max(m - 1, 0)
            if isinstance(m, int)
            else tf.maximum(m - 1, 0)
        )
        x1 = tf.pad(x1, [[pad, pad]])  # pad input with zeros
        x1, x2 = _pack(x1, x2)
        out = tf.nn.conv1d(x1, x2, stride=1, padding="VALID")
        return tf.squeeze(out, axis=[0, 2])

    n = shape_op(x1)[0]
    m = shape_op(x2)[0]

    if mode == "full":
        return _full_corr(x1, x2)
    elif mode == "same":
        # unfortunately we can't leverage 'SAME' padding directly like
        # we can with "valid"
        # it works fine for odd-length filters, but for even-length filters
        # the output is off by 1 compared to numpy, due to how
        # tf handles centering
        full_corr = _full_corr(x1, x2)
        full_len = n + m - 1
        out_len = (
            max([n, m])
            if isinstance(n, int) and isinstance(m, int)
            else tf.maximum(n, m)
        )
        start = (full_len - out_len) // 2
        return tf.slice(full_corr, [start], [out_len])
    elif mode == "valid":
        x1, x2 = _pack(x1, x2)
        return tf.squeeze(
            tf.nn.conv1d(x1, x2, stride=1, padding="VALID"), axis=[0, 2]
        )
    else:
        raise ValueError(
            f"Invalid mode: '{mode}'. Mode must be one of:"
            f" 'full', 'same', 'valid'."
        )