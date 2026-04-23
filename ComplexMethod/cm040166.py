def pool3d(
    x,
    pool_size,
    strides=(1, 1, 1),
    padding="valid",
    data_format=None,
    pool_mode="max",
):
    """DEPRECATED."""
    if data_format is None:
        data_format = backend.image_data_format()
    if data_format not in {"channels_first", "channels_last"}:
        raise ValueError(f"Unknown data_format: {data_format}")

    x, tf_data_format = _preprocess_conv3d_input(x, data_format)
    padding = _preprocess_padding(padding)
    if tf_data_format == "NDHWC":
        strides = (1,) + strides + (1,)
        pool_size = (1,) + pool_size + (1,)
    else:
        strides = (1, 1) + strides
        pool_size = (1, 1) + pool_size

    if pool_mode == "max":
        x = tf.nn.max_pool3d(
            x, pool_size, strides, padding=padding, data_format=tf_data_format
        )
    elif pool_mode == "avg":
        x = tf.nn.avg_pool3d(
            x, pool_size, strides, padding=padding, data_format=tf_data_format
        )
    else:
        raise ValueError(f"Invalid pooling mode: {str(pool_mode)}")

    if data_format == "channels_first" and tf_data_format == "NDHWC":
        x = tf.transpose(x, (0, 4, 1, 2, 3))
    return x