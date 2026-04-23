def bias_add(x, bias, data_format=None):
    """DEPRECATED."""
    if data_format is None:
        data_format = backend.image_data_format()
    if data_format not in {"channels_first", "channels_last"}:
        raise ValueError(f"Unknown data_format: {data_format}")
    bias_shape = bias.shape
    if len(bias_shape) != 1 and len(bias_shape) != ndim(x) - 1:
        raise ValueError(
            f"Unexpected bias dimensions {len(bias_shape)}. "
            f"Expected it to be 1 or {ndim(x) - 1} dimensions"
        )

    if len(bias_shape) == 1:
        if data_format == "channels_first":
            return tf.nn.bias_add(x, bias, data_format="NCHW")
        return tf.nn.bias_add(x, bias, data_format="NHWC")
    if ndim(x) in (3, 4, 5):
        if data_format == "channels_first":
            bias_reshape_axis = (1, bias_shape[-1]) + bias_shape[:-1]
            return x + reshape(bias, bias_reshape_axis)
        return x + reshape(bias, (1,) + bias_shape)
    return tf.nn.bias_add(x, bias)