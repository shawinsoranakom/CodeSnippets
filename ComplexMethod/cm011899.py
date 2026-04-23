def _prepare_convolution_fusion_create(
    cls,
    x: "TensorBox",
    weight: "TensorBox",
    bias: "TensorBox",
    padding: Sequence[int],
    stride: Sequence[int],
    dilation: Sequence[int],
    groups: int,
    transposed: bool = False,
    output_padding: Sequence[int] | None = None,
    quantize_args: list["TensorBox"] | None = None,
    other: Optional["TensorBox"] = None,
):
    """
    This function is a helper function to prepare inputs, layout and constant args
    for convolution post-op fusion's create function, including deciding the output
    layout (channels first or channels last), realizing inputs and make them etc. The
    function only supports the CPU/XPU device since conv post-op fusion kernel is only
    supported on CPU/XPU right now.
    """

    # Port from aten/src/ATen/native/ConvUtils.h: _conv_input_size
    def _conv_input_size(
        output_size, weight_size, padding, output_padding, stride, dilation, groups
    ):
        assert len(output_size) == len(weight_size), "Expect input dim == weight dim"
        dim = len(output_size)
        assert dim > 2, "Expect input dim > 2"

        BATCH_DIM = 0
        WEIGHT_INPUT_CHANNELS_DIM = 1
        input_size = []
        input_size.append(output_size[BATCH_DIM])
        input_size.append(weight_size[WEIGHT_INPUT_CHANNELS_DIM] * groups)
        for d in range(2, dim):
            kernel = (weight_size[d] - 1) * dilation[d - 2] + 1
            input_size_d = (
                (output_size[d] - 1) * stride[d - 2]
                - (padding[d - 2] * 2)
                + kernel
                + output_padding[d - 2]
            )
            input_size.append(input_size_d)
        return list(map(int, input_size))

    # Port from aten/src/ATen/native/ConvUtils.h: _conv_output_size
    def _conv_output_size(input_size, weight_size, padding, stride, dilation=None):
        has_dilation = dilation is not None
        dim = len(input_size)
        output_size = []
        output_size.append(input_size[0])
        output_size.append(weight_size[0])
        for d in range(2, dim):
            # pyrefly: ignore [unsupported-operation]
            dilation_ = dilation[d - 2] if has_dilation else 1
            kernel = dilation_ * (weight_size[d] - 1) + 1
            output_size_d = (input_size[d] + (2 * padding[d - 2]) - kernel) // stride[
                d - 2
            ] + 1
            output_size.append(output_size_d)
        return output_size

    # The size of prepacked_weight is the prepacked weight size of deconv:
    #   Groups > 1:  [g*o, i/g, ...]
    #   Groups == 1: [o, i, ...]
    # Returns original weight size in [i, o, ...]
    def _original_deconv_weight_size(
        prepacked_weight,
        groups,
    ):
        prepacked_weight_size = prepacked_weight.size()
        dim = len(prepacked_weight_size)
        assert dim > 2, "Expect weight dim > 2"
        if groups > 1:
            weight_size = []
            weight_size.append(prepacked_weight_size[1] * groups)
            weight_size.append(prepacked_weight_size[0] / groups)
            weight_size.extend(prepacked_weight_size[d] for d in range(2, dim))
        else:
            weight_size = prepacked_weight.transpose(0, 1).size()
        return weight_size

    x.realize()
    weight.realize()
    if bias is not None:
        bias.realize()
    with V.graph.fake_mode:
        # TODO <Leslie> cleaned up the fake_tensor trace as Linear implementation
        x_fake = ir_node_to_tensor(x)
        weight_fake = ir_node_to_tensor(weight)
        dims = len(x_fake.size()) - 2
        assert 0 < len(padding) <= dims
        assert 0 < len(dilation) <= dims
        assert 0 < len(stride) <= dims
        padding = pad_listlike(padding, dims)
        dilation = pad_listlike(dilation, dims)
        stride = pad_listlike(stride, dims)
        if output_padding is None:
            output_padding = pad_listlike([0], dims)
        else:
            assert 0 < len(output_padding) <= dims
            output_padding = pad_listlike(output_padding, dims)
        assert isinstance(groups, (int, sympy.core.numbers.Integer))
        if transposed:
            # When transposed, the size of the prepacked oneDNN weight is different
            # from the PyTorch weight. We're not able to run aten conv with such
            # size. We infer the output size from the input params here:
            weight_size = _original_deconv_weight_size(weight_fake, groups)
            input_size = x_fake.size()
            output_size = _conv_input_size(
                input_size,
                weight_size,
                padding,
                output_padding,
                stride,
                dilation,
                groups,
            )
        else:
            x_shape = list(x_fake.shape)
            weight_shape = list(weight_fake.shape)
            if len(x_shape) != len(weight_shape):
                assert len(x_shape) == 3 and len(weight_shape) == 4
                weight_shape.pop(2)
            output_size = _conv_output_size(
                x_shape,
                weight_shape,
                padding,
                stride,
                dilation,
            )

        req_stride_order = [0] + list(reversed(range(1, len(stride) + 1)))
        req_stride_order = [len(req_stride_order)] + req_stride_order

    x = cls.require_stride_order(x, req_stride_order)

    # We won't do weight prepack for Conv if dynamic_shapes or if is xpu.
    # In static shape cases, since weight is prepacked, we'll always force output to be channels last in the Conv kernel.
    # In dynamic shape cases, for input with channels = 1, like tensor of size (s0, 1, 28, 28) and stride (784, 784, 28, 1),
    # x = cls.require_stride_order(x, req_stride_order) where req_stride_order is in the channels last order
    # won't change the stride of this tensor since stride for dimensions of size 1 is ignored. While in Conv kernel,
    # this tensor is considered as channels first and the output will be in contiguous format.
    # To align the behavior of the Conv kernel, we set the output_stride in such case to be contiguous instead of channels last.
    dynamic_shapes = not all(isinstance(i, int) for i in (output_size))
    if (
        dynamic_shapes or get_device_type(x) == "xpu"
    ) and is_contiguous_storage_and_layout(x):
        output_stride: StrideType = FlexibleLayout.contiguous_strides(output_size)
    # Currently we don't support channel last for the situation that stride of input's batch dim is 0,
    # eg. input_size = (1, 1280, 64, 64), but input_stride=(0, 1, 81920, 1280).
    # So we use NCHW hear instead.
    # Different with cpu, cpu conv always use channels_last for convolution when weight is prepacked,
    # but xpu does not do the prepack, so the problem exposed here is only for xpu.
    # TODO support channels_last for such zero stride input.
    elif get_device_type(x) == "xpu" and x.get_stride()[0] == 0:
        output_stride = FlexibleLayout.contiguous_strides(output_size)
    else:
        output_stride = make_channels_last_strides_for(output_size)

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
        other = cls.require_stride_order(other, req_stride_order)
        assert isinstance(other, TensorBox)
        inputs += [other]

    kernel_layout = FixedLayout(
        x.get_device_or_error(),
        x.get_dtype(),
        convert_shape_to_inductor(output_size),
        convert_shape_to_inductor(output_stride),
    )
    constant_args = [padding, stride, dilation, groups]
    if transposed:
        constant_args.insert(1, output_padding)

    if bias is not None:
        inputs.append(bias)
    else:
        constant_args.insert(0, bias)
    return inputs, constant_args, kernel_layout, req_stride_order, other