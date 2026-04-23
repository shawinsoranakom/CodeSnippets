def pool2d(
    x,
    pool_size,
    strides=(1, 1),
    padding="valid",
    data_format=None,
    pool_mode="max",
):
    """DEPRECATED."""
    if data_format is None:
        data_format = backend.image_data_format()
    if data_format not in {"channels_first", "channels_last"}:
        raise ValueError(f"Unknown data_format: {data_format}")
    if len(pool_size) != 2:
        raise ValueError("`pool_size` must be a tuple of 2 integers.")
    if len(strides) != 2:
        raise ValueError("`strides` must be a tuple of 2 integers.")

    x, tf_data_format = _preprocess_conv2d_input(x, data_format)
    padding = _preprocess_padding(padding)
    if tf_data_format == "NHWC":
        strides = (1,) + strides + (1,)
        pool_size = (1,) + pool_size + (1,)
    else:
        strides = (1, 1) + strides
        pool_size = (1, 1) + pool_size

    if pool_mode == "max":
        x = tf.compat.v1.nn.max_pool(
            x, pool_size, strides, padding=padding, data_format=tf_data_format
        )
    elif pool_mode == "avg":
        x = tf.compat.v1.nn.avg_pool(
            x, pool_size, strides, padding=padding, data_format=tf_data_format
        )
    else:
        raise ValueError(f"Invalid pooling mode: {str(pool_mode)}")

    if data_format == "channels_first" and tf_data_format == "NHWC":
        x = tf.transpose(x, (0, 3, 1, 2))  # NHWC -> NCHW
    return x