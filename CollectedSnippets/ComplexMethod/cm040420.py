def depthwise_conv(
    inputs,
    kernel,
    strides=1,
    padding="valid",
    data_format=None,
    dilation_rate=1,
):
    data_format = backend.standardize_data_format(data_format)
    num_spatial_dims = len(inputs.shape) - 2
    if num_spatial_dims > 2:
        raise ValueError(
            "`inputs` rank must be 3 (1D conv) or 4 (2D conv). Received: "
            f"{inputs.ndim}."
        )
    # Because we use `tf.nn.depthwise_conv2d` for both 1D and 2D convs, we set
    # `tf_data_format` using 2D conv format.
    tf_data_format = _convert_data_format(data_format, 4)
    padding = padding.upper()
    if isinstance(strides, int):
        strides = (strides,) * num_spatial_dims
    if isinstance(dilation_rate, int):
        dilation_rate = (dilation_rate,) * num_spatial_dims
    if num_spatial_dims == 1:
        # 1D depthwise conv.
        # `tf.nn.depthwise_conv2d` does not support `channels_first` with
        # dilations on CPU. Transpose to `channels_last`, compute, and
        # transpose back to avoid the limitation.
        need_transpose = data_format == "channels_first" and all(
            d.device_type == "CPU" for d in tf.config.list_logical_devices()
        )
        if need_transpose:
            inputs = _transpose_spatial_inputs(inputs)
        if need_transpose or data_format == "channels_last":
            strides = (1,) + strides * 2 + (1,)
            spatial_start_dim = 1
        else:
            strides = (1, 1) + strides * 2
            spatial_start_dim = 2
        inputs = tf.expand_dims(inputs, spatial_start_dim)
        kernel = tf.expand_dims(kernel, axis=0)

        dilation_rate = None if dilation_rate is None else (1,) + dilation_rate

        if need_transpose or data_format == "channels_last":
            conv_data_format = _convert_data_format("channels_last", 4)
        else:
            conv_data_format = _convert_data_format("channels_first", 4)
        outputs = tf.nn.depthwise_conv2d(
            inputs,
            kernel,
            strides,
            padding,
            data_format=conv_data_format,
            dilations=dilation_rate,
        )
        outputs = tf.squeeze(outputs, [spatial_start_dim])
        if need_transpose:
            outputs = _transpose_spatial_outputs(outputs)
        return outputs

    if data_format == "channels_last":
        strides = (1,) + strides + (1,)
        spatial_start_dim = 1
    else:
        strides = (1, 1) + strides
        spatial_start_dim = 2
    return tf.nn.depthwise_conv2d(
        inputs,
        kernel,
        strides,
        padding,
        data_format=tf_data_format,
        dilations=dilation_rate,
    )