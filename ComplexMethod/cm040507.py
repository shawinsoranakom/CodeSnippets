def conv_transpose(
    inputs,
    kernel,
    strides=1,
    padding="valid",
    output_padding=None,
    data_format=None,
    dilation_rate=1,
):
    inputs = get_ov_output(inputs)
    kernel = get_ov_output(kernel)

    data_format = backend.standardize_data_format(data_format)
    num_spatial_dims = inputs.get_partial_shape().rank.get_length() - 2

    strides = _adjust_strides_dilation(strides, num_spatial_dims)
    dilation_rate = _adjust_strides_dilation(dilation_rate, num_spatial_dims)

    # Convert to channels-first (NCHW) layout
    inputs = _adjust_input(inputs, num_spatial_dims, data_format)
    # Rearrange kernel from Keras (*kernel, C_out, C_in)
    # to OpenVINO format (C_in, C_out, *kernel)
    kernel = _adjust_kernel(kernel, num_spatial_dims)

    # inputs: (N, C_in, *spatial), kernel: (C_in, C_out, *kernel_size)
    input_pshape = inputs.get_partial_shape()
    kernel_pshape = kernel.get_partial_shape()

    spatial_output_shape = []
    all_static = True
    for i in range(num_spatial_dims):
        in_dim = input_pshape[2 + i]
        k_dim = kernel_pshape[2 + i]
        s = strides[i]
        d = dilation_rate[i]
        op_i = (
            output_padding
            if output_padding is None or isinstance(output_padding, int)
            else output_padding[i]
        )
        if in_dim.is_static and k_dim.is_static:
            out_dim = _get_output_shape_given_tf_padding(
                input_size=in_dim.get_length(),
                kernel_size=k_dim.get_length(),
                strides=s,
                padding=padding,
                output_padding=op_i,
                dilation_rate=d,
            )
            spatial_output_shape.append(out_dim)
        else:
            all_static = False
            break

    pad_mode = "SAME_LOWER" if padding.lower() == "same" else "VALID"

    if all_static:
        output_shape_node = ov_opset.constant(
            spatial_output_shape, Type.i64
        ).output(0)
    else:
        output_shape_node = None

    conv_t = ov_opset.convolution_backprop_data(
        inputs,
        kernel,
        strides=strides,
        output_shape=output_shape_node,
        dilations=dilation_rate,
        auto_pad=pad_mode,
    )
    result = _adjust_outputs(conv_t.output(0), num_spatial_dims, data_format)
    return OpenVINOKerasTensor(result)