def conv(
    inputs,
    kernel,
    strides=1,
    padding="valid",
    data_format=None,
    dilation_rate=1,
):
    """Convolution with fixed group handling."""
    inputs = convert_to_tensor(inputs)
    kernel = convert_to_tensor(kernel)
    num_spatial_dims = inputs.ndim - 2
    strides = standardize_tuple(strides, num_spatial_dims, "strides")

    data_format = backend.standardize_data_format(data_format)
    if data_format == "channels_last":
        inputs = _transpose_spatial_inputs(inputs)

    kernel = _transpose_conv_kernel(kernel)

    if data_format == "channels_last":
        inputs = _maybe_convert_to_channels_last(inputs)
        kernel = _maybe_convert_to_channels_last(kernel)

    # calc. groups snippet
    in_channels = inputs.shape[1]
    kernel_in_channels = kernel.shape[1]
    if in_channels % kernel_in_channels != 0:
        raise ValueError(
            f"Input channels ({in_channels}) must be divisible by "
            f"kernel input channels ({kernel_in_channels})"
        )
    groups = in_channels // kernel_in_channels

    # handle padding
    if padding == "same":
        inputs, padding = _apply_same_padding(
            inputs,
            kernel.shape[2:],
            strides,
            data_format,
            "conv",
            dilation_rate,
        )
    else:
        padding = 0

    # apply convolution
    if num_spatial_dims == 1:
        outputs = tnn.conv1d(
            inputs,
            kernel,
            stride=strides,
            padding=padding,
            dilation=dilation_rate,
            groups=groups,
        )
    elif num_spatial_dims == 2:
        outputs = tnn.conv2d(
            inputs,
            kernel,
            stride=strides,
            padding=padding,
            dilation=dilation_rate,
            groups=groups,
        )
    elif num_spatial_dims == 3:
        outputs = tnn.conv3d(
            inputs,
            kernel,
            stride=strides,
            padding=padding,
            dilation=dilation_rate,
            groups=groups,
        )
    else:
        raise ValueError(
            "Inputs to conv operation should have ndim=3, 4, or 5,"
            "corresponding to 1D, 2D and 3D inputs. Received input "
            f"shape: {inputs.shape}."
        )

    if data_format == "channels_last":
        outputs = _transpose_spatial_outputs(outputs)
    return outputs