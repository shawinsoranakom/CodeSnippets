def average_pool(
    inputs,
    pool_size,
    strides=None,
    padding="valid",
    data_format=None,
):
    """Fixed average pooling with correct padding calculation."""
    inputs = convert_to_tensor(inputs)
    num_spatial_dims = inputs.ndim - 2
    pool_size = standardize_tuple(pool_size, num_spatial_dims, "pool_size")
    strides = (
        pool_size
        if strides is None
        else standardize_tuple(strides, num_spatial_dims, "strides")
    )

    data_format = backend.standardize_data_format(data_format)
    orig_format = data_format

    if data_format == "channels_last":
        inputs = _transpose_spatial_inputs(inputs)

    if padding == "same":
        # Torch does not natively support `"same"` padding, we need to manually
        # apply the right amount of padding to `inputs`.
        inputs, padding = _apply_same_padding(
            inputs,
            pool_size,
            strides,
            "channels_first",  # we're in channels_first here
            "pooling",
        )
    else:
        padding = 0

    # apply pooling
    if num_spatial_dims == 1:
        outputs = tnn.avg_pool1d(
            inputs,
            kernel_size=pool_size,
            stride=strides,
            padding=padding,
            count_include_pad=False,
        )
    elif num_spatial_dims == 2:
        outputs = tnn.avg_pool2d(
            inputs,
            kernel_size=pool_size,
            stride=strides,
            padding=padding,
            count_include_pad=False,
        )
    elif num_spatial_dims == 3:
        outputs = tnn.avg_pool3d(
            inputs,
            kernel_size=pool_size,
            stride=strides,
            padding=padding,
            count_include_pad=False,
        )
    else:
        raise ValueError(
            "Inputs to pooling op must have ndim=3, 4 or 5, "
            "corresponding to 1D, 2D and 3D inputs. "
            f"Received input shape: {inputs.shape}."
        )

    if orig_format == "channels_last":
        outputs = _transpose_spatial_outputs(outputs)

    return outputs