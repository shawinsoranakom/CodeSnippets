def conv_transpose(
    inputs,
    kernel,
    strides=1,
    padding="valid",
    output_padding=None,
    data_format=None,
    dilation_rate=1,
):
    inputs = convert_to_tensor(inputs)
    kernel = convert_to_tensor(kernel)
    num_spatial_dims = inputs.ndim - 2
    strides = standardize_tuple(strides, num_spatial_dims, "strides")

    data_format = backend.standardize_data_format(data_format)
    (
        torch_padding,
        torch_output_padding,
    ) = compute_conv_transpose_padding_args_for_torch(
        input_shape=inputs.shape,
        kernel_shape=kernel.shape,
        strides=strides,
        padding=padding,
        output_padding=output_padding,
        dilation_rate=dilation_rate,
    )
    if data_format == "channels_last":
        inputs = _transpose_spatial_inputs(inputs)
    # Transpose kernel from keras format to torch format.
    kernel = _transpose_conv_kernel(kernel)

    if data_format == "channels_last":
        inputs = _maybe_convert_to_channels_last(inputs)
        kernel = _maybe_convert_to_channels_last(kernel)

    kernel_spatial_shape = kernel.shape[2:]
    if isinstance(dilation_rate, int):
        dilation_rate = [dilation_rate] * len(kernel_spatial_shape)

    if num_spatial_dims == 1:
        outputs = tnn.conv_transpose1d(
            inputs,
            kernel,
            stride=strides,
            padding=torch_padding,
            output_padding=torch_output_padding,
            dilation=dilation_rate,
        )
    elif num_spatial_dims == 2:
        outputs = tnn.conv_transpose2d(
            inputs,
            kernel,
            stride=strides,
            padding=torch_padding,
            output_padding=torch_output_padding,
            dilation=dilation_rate,
        )
    elif num_spatial_dims == 3:
        outputs = tnn.conv_transpose3d(
            inputs,
            kernel,
            stride=strides,
            padding=torch_padding,
            output_padding=torch_output_padding,
            dilation=dilation_rate,
        )
    else:
        raise ValueError(
            "Inputs to conv transpose operation should have ndim=3, 4, or 5,"
            "corresponding to 1D, 2D and 3D inputs. Received input "
            f"shape: {inputs.shape}."
        )
    if data_format == "channels_last":
        outputs = _transpose_spatial_outputs(outputs)
    return outputs