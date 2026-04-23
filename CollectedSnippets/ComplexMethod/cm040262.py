def _inverted_res_block(
    x, expansion, filters, kernel_size, stride, se_ratio, activation, block_id
):
    channel_axis = 1 if backend.image_data_format() == "channels_first" else -1
    shortcut = x
    prefix = "expanded_conv_"
    infilters = x.shape[channel_axis]
    if block_id:
        # Expand
        prefix = f"expanded_conv_{block_id}_"
        x = layers.Conv2D(
            _depth(infilters * expansion),
            kernel_size=1,
            padding="same",
            use_bias=False,
            name=f"{prefix}expand",
        )(x)
        x = layers.BatchNormalization(
            axis=channel_axis,
            epsilon=1e-3,
            momentum=0.999,
            name=f"{prefix}expand_bn",
        )(x)
        x = activation(x)

    if stride == 2:
        x = layers.ZeroPadding2D(
            padding=imagenet_utils.correct_pad(x, kernel_size),
            name=f"{prefix}depthwise_pad",
        )(x)
    x = layers.DepthwiseConv2D(
        kernel_size,
        strides=stride,
        padding="same" if stride == 1 else "valid",
        use_bias=False,
        name=f"{prefix}depthwise",
    )(x)
    x = layers.BatchNormalization(
        axis=channel_axis,
        epsilon=1e-3,
        momentum=0.999,
        name=f"{prefix}depthwise_bn",
    )(x)
    x = activation(x)

    if se_ratio:
        x = _se_block(x, _depth(infilters * expansion), se_ratio, prefix)

    x = layers.Conv2D(
        filters,
        kernel_size=1,
        padding="same",
        use_bias=False,
        name=f"{prefix}project",
    )(x)
    x = layers.BatchNormalization(
        axis=channel_axis,
        epsilon=1e-3,
        momentum=0.999,
        name=f"{prefix}project_bn",
    )(x)

    if stride == 1 and infilters == filters:
        x = layers.Add(name=f"{prefix}add")([shortcut, x])
    return x