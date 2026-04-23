def _apply_same_padding(
    inputs, kernel_size, strides, data_format, operation_type, dilation_rate=1
):
    """Apply same padding to the input tensor.

    This function will evaluate if the padding value is compatible with torch
    functions. To avoid calling `pad()` as much as possible, which may cause
    performance or memory issues, when compatible, it does not apply the padding
    to the tensor, but returns the input tensor and the padding value to pass to
    the torch functions. If not compatible, it returns the padded tensor and 0
    as the padding value.

    Returns:
        tensor: A padded tensor or the inputs.
        padding: The padding value, ready to pass to the torch functions.
    """
    spatial_shape = inputs.shape[2:]
    num_spatial_dims = len(spatial_shape)
    padding = []

    if operation_type != "pooling":
        dilation_rate = standardize_tuple(
            dilation_rate, num_spatial_dims, "dilation_rate"
        )

    for i in range(num_spatial_dims):
        dil = 1 if operation_type == "pooling" else dilation_rate[i]
        pad = _compute_padding_length(
            spatial_shape[i], kernel_size[i], strides[i], dil
        )
        padding.append(pad)

    # convert padding to torch format
    if all(left == right for left, right in padding):
        return inputs, [left for left, _ in padding]

    # else, need to pad manually
    flattened_padding = []
    for pad in reversed(padding):
        flattened_padding.extend(pad)

    mode = "replicate" if operation_type == "pooling" else "constant"
    return tnn.pad(inputs, pad=tuple(flattened_padding), mode=mode), 0