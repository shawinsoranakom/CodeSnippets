def _prepare_linear_fusion_create(
    cls,
    x: "TensorBox",
    weight: "TensorBox",
    bias: "TensorBox",
    quantize_args: list["TensorBox"] | None = None,
    other: Optional["TensorBox"] = None,
    binary_sum: bool = False,
):
    """
    This function is a helper function to prepare inputs, layout and constant args
    for linear post-op fusion's create function. The function only supports the CPU device
    since linear post-op fusion kernel is only supported on CPU right now.
    """
    x.realize()
    weight.realize()
    if bias is not None:
        bias.realize()

    *m, _ = x.get_size()
    # The weight has been transposed during the qlinear weight prepack process.
    # https://github.com/pytorch/pytorch/blob/4979f9c0d72490970e2019bb1d2284f83d93f76b/
    # aten/src/ATen/native/quantized/cpu/qlinear_prepack.cpp#L291
    _, oc = weight.get_size()
    output_size = list(m) + [oc]
    req_stride_order = list(reversed(range(len(x.get_size()))))

    x = cls.require_stride_order(x, req_stride_order)
    assert get_device_type(x) == get_device_type(weight)
    assert get_device_type(x) in SUPPORTED_MKLDNN_DEVICES
    inputs = [x]

    if quantize_args is not None:
        x_scale, x_zero_point, w_scale, w_zero_point = quantize_args
        x_scale.realize()
        x_zero_point.realize()
        w_scale.realize()
        w_zero_point.realize()
        inputs = inputs + [x_scale, x_zero_point] + [weight] + [w_scale, w_zero_point]
    else:
        inputs += [weight]

    if other is not None:
        if binary_sum:
            other = cls.require_stride_order(other, req_stride_order)
        inputs = inputs + [other]

    output_stride = FlexibleLayout.contiguous_strides(output_size)
    kernel_layout = FixedLayout(
        x.get_device(),
        x.get_dtype(),
        output_size,
        output_stride,
    )
    constant_args: list[Any] = []

    if bias is not None:
        inputs.append(bias)
    else:
        constant_args.insert(0, bias)
    return inputs, constant_args, kernel_layout, req_stride_order, other