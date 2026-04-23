def adaptive_average_pool(inputs, output_size, data_format=None):
    """Adaptive average pooling(1D/2D/3D) with channels_last support."""
    inputs = convert_to_tensor(inputs)
    num_spatial_dims = inputs.ndim - 2

    data_format = backend.standardize_data_format(data_format)
    orig_format = data_format
    if data_format == "channels_last":
        inputs = _transpose_spatial_inputs(inputs)

    if isinstance(output_size, int):
        torch_output_size = (
            output_size
            if num_spatial_dims == 1
            else (output_size,) * num_spatial_dims
        )
    else:
        torch_output_size = standardize_tuple(
            output_size, num_spatial_dims, "output_size"
        )

    if get_device() == "meta":
        inputs = torch.empty(
            size=inputs.shape, dtype=inputs.dtype, device="cpu"
        )

    if num_spatial_dims == 1:
        outputs = tnn.adaptive_avg_pool1d(inputs, output_size=torch_output_size)
    elif num_spatial_dims == 2:
        outputs = tnn.adaptive_avg_pool2d(inputs, output_size=torch_output_size)
    elif num_spatial_dims == 3:
        outputs = tnn.adaptive_avg_pool3d(inputs, output_size=torch_output_size)
    else:
        raise ValueError(
            "Inputs to adaptive average pooling must have ndim=3, 4 or 5, "
            f"Received input shape: {inputs.shape}."
        )

    if orig_format == "channels_last":
        outputs = _transpose_spatial_outputs(outputs)
    return outputs