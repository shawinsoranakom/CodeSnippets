def separable_conv2d(
    x,
    depthwise_kernel,
    pointwise_kernel,
    strides=(1, 1),
    padding="valid",
    data_format=None,
    dilation_rate=(1, 1),
):
    """DEPRECATED."""
    if data_format is None:
        data_format = backend.image_data_format()
    if data_format not in {"channels_first", "channels_last"}:
        raise ValueError(f"Unknown data_format: {data_format}")
    if len(strides) != 2:
        raise ValueError("`strides` must be a tuple of 2 integers.")

    x, tf_data_format = _preprocess_conv2d_input(x, data_format)
    padding = _preprocess_padding(padding)
    if not isinstance(strides, tuple):
        strides = tuple(strides)
    if tf_data_format == "NHWC":
        strides = (1,) + strides + (1,)
    else:
        strides = (1, 1) + strides

    x = tf.nn.separable_conv2d(
        x,
        depthwise_kernel,
        pointwise_kernel,
        strides=strides,
        padding=padding,
        dilations=dilation_rate,
        data_format=tf_data_format,
    )
    if data_format == "channels_first" and tf_data_format == "NHWC":
        x = tf.transpose(x, (0, 3, 1, 2))  # NHWC -> NCHW
    return x