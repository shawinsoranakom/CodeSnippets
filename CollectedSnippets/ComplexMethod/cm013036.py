def _convolution(
    g: jit_utils.GraphContext,
    input,
    weight,
    bias,
    stride,
    padding,
    dilation,
    transposed,
    output_padding,
    groups,
    benchmark,
    deterministic,
    cudnn_enabled,
    allow_tf32=None,
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

    kwargs = {
        "kernel_shape_i": weight_size[2:],
        "strides_i": stride,
        # NB: ONNX supports asymmetric padding, whereas PyTorch supports only
        # symmetric padding
        "pads_i": padding + padding,
        "dilations_i": dilation,
        "group_i": groups,
    }

    if any(o != 0 for o in output_padding):
        # ONNX supports both output_shape and output_padding. they are equivalent expressive.
        # output_padding is more straightforward, so we use it here.
        # output_shape = stride * (input_shape - 1) + output_padding + kernel_shape - padding * 2
        if not transposed:
            raise AssertionError("output_padding requires transposed=True")
        if len(stride) != len(output_padding):
            raise AssertionError(
                f"len(stride)={len(stride)} != len(output_padding)={len(output_padding)}"
            )
        kwargs["output_padding_i"] = output_padding

    n = g.op("ConvTranspose" if transposed else "Conv", *args, **kwargs)

    if (
        not symbolic_helper._is_none(bias)
        and symbolic_helper._get_tensor_rank(bias) != 1
    ):
        return g.op("Add", n, bias)
    else:
        return n