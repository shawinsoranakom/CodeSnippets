def _convolution_mode(
    g: jit_utils.GraphContext,
    input,
    weight,
    bias,
    stride,
    padding,
    dilation,
    groups,
):
    weight_size = symbolic_helper._get_tensor_sizes(weight)
    try:
        kernel_shape = weight_size[2:]
    except Exception:
        # FIXME(justinchuby): Avoid catching Exception.
        # Catch a more specific exception instead.
        kernel_shape = None

    if kernel_shape is None or any(i is None for i in kernel_shape):
        raise errors.SymbolicValueError(
            "Unsupported: ONNX export of convolution for kernel of unknown shape.",
            input,
        )

    args = [input, weight]
    # ONNX only supports 1D bias
    if (
        not symbolic_helper._is_none(bias)
        and symbolic_helper._get_tensor_rank(bias) == 1
    ):
        args.append(bias)

    if padding == "valid":
        padding = "VALID"
    elif padding == "same":
        padding = "SAME_UPPER"
    kwargs = {
        "kernel_shape_i": weight_size[2:],
        "strides_i": stride,
        "auto_pad_s": padding,
        "dilations_i": dilation,
        "group_i": groups,
    }

    n = g.op("Conv", *args, **kwargs)

    if (
        not symbolic_helper._is_none(bias)
        and symbolic_helper._get_tensor_rank(bias) != 1
    ):
        return g.op("Add", n, bias)
    else:
        return n