def conv2d_transpose(
    x,
    kernel,
    output_shape,
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

    # `atrous_conv2d_transpose` only supports NHWC format, even on GPU.
    if data_format == "channels_first" and dilation_rate != (1, 1):
        force_transpose = True
    else:
        force_transpose = False

    x, tf_data_format = _preprocess_conv2d_input(
        x, data_format, force_transpose
    )

    if data_format == "channels_first" and tf_data_format == "NHWC":
        output_shape = (
            output_shape[0],
            output_shape[2],
            output_shape[3],
            output_shape[1],
        )
    if output_shape[0] is None:
        output_shape = (tf.shape(x)[0],) + tuple(output_shape[1:])

    if isinstance(output_shape, (tuple, list)):
        output_shape = tf.stack(list(output_shape))

    padding = _preprocess_padding(padding)
    if tf_data_format == "NHWC":
        strides = (1,) + strides + (1,)
    else:
        strides = (1, 1) + strides

    if dilation_rate == (1, 1):
        x = tf.compat.v1.nn.conv2d_transpose(
            x,
            kernel,
            output_shape,
            strides,
            padding=padding,
            data_format=tf_data_format,
        )
    else:
        if dilation_rate[0] != dilation_rate[1]:
            raise ValueError(
                "Expected the 2 dimensions of the `dilation_rate` argument "
                "to be equal to each other. "
                f"Received: dilation_rate={dilation_rate}"
            )
        x = tf.nn.atrous_conv2d_transpose(
            x, kernel, output_shape, rate=dilation_rate[0], padding=padding
        )
    if data_format == "channels_first" and tf_data_format == "NHWC":
        x = tf.transpose(x, (0, 3, 1, 2))  # NHWC -> NCHW
    return x