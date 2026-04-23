def add(x1, x2):
    if not isinstance(x1, (int, float)):
        x1 = convert_to_tensor(x1)
    if not isinstance(x2, (int, float)):
        x2 = convert_to_tensor(x2)
    dtype = dtypes.result_type(
        getattr(x1, "dtype", type(x1)),
        getattr(x2, "dtype", type(x2)),
    )
    x1 = convert_to_tensor(x1, dtype)
    x2 = convert_to_tensor(x2, dtype)

    # Special case of `tf.add`: `tf.nn.bias_add`
    # `BiasAdd` can be fused with `MatMul` and `Conv*` kernels
    # Expecting `x1` to be `inputs` and `x2` to be `bias` (no swapping)
    x2_squeeze_shape = [d for d in x2.shape.as_list() if d is None or d > 1]
    if (
        # `x2` looks like bias (can be squeezed to vector)
        1 == len(x2_squeeze_shape)
        # `x1` looks like input tensor (rank >= 2)
        and len(x1.shape) > 1
        # `x2` non-squeezable dimension defined
        and x2_squeeze_shape[0] is not None
        # `x2` non-squeezable dimension match `x1` channel dimension
        and x2_squeeze_shape[0]
        in {x1.shape.as_list()[1], x1.shape.as_list()[-1]}
    ):
        if x1.shape[-1] == x2_squeeze_shape[0]:
            data_format = "NHWC"
        else:
            data_format = "NCHW"
        if len(x2.shape) > 1:
            x2 = tf.squeeze(x2)
        return tf.nn.bias_add(x1, x2, data_format=data_format)

    return tf.add(x1, x2)