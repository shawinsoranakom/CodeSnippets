def convolution_rules(op_schema: OpSchema) -> OutputSharding:
    (
        input_spec,
        weight_spec,
        bias_spec,
        stride,
        padding,
        dilation,
        _transposed,
        _output_padding,
        _groups,
    ) = op_schema.args_schema

    if not isinstance(input_spec, DTensorSpec):
        raise AssertionError
    if not isinstance(weight_spec, DTensorSpec):
        raise AssertionError
    # bias_spec can be None (optional parameter in aten.convolution schema)
    if bias_spec is not None:
        if not isinstance(bias_spec, DTensorSpec):
            raise AssertionError
    if input_spec.tensor_meta is None:
        raise AssertionError
    if weight_spec.tensor_meta is None:
        raise AssertionError
    in_shape = input_spec.tensor_meta.shape
    weight_shape = weight_spec.tensor_meta.shape
    if not isinstance(stride, list):
        raise AssertionError(f"stride must be list, got {type(stride)}")
    if not isinstance(padding, list):
        raise AssertionError(f"padding must be list, got {type(padding)}")
    if not isinstance(dilation, list):
        raise AssertionError(f"dilation must be list, got {type(dilation)}")
    # weight_shape might not be torch.Size in all cases (e.g., SymIntArrayRef during tracing)
    # so we don't assert its type, just use it
    out_conv_shape = [
        (d + 2 * padding[i] - dilation[i] * (weight_shape[i + 1] - 1) - 1) // stride[i]
        + 1
        for (i, d) in enumerate(in_shape[2:])
    ]
    output_shape = [in_shape[0], weight_shape[0]] + out_conv_shape
    output_stride = [1]
    for i in range(1, len(output_shape)):
        output_stride.insert(0, output_stride[0] * output_shape[-i])
    output_dim_map = input_spec.dim_map
    pending_sums = input_spec.sums

    tensor_meta = TensorMeta(
        torch.Size(output_shape),
        tuple(output_stride),
        input_spec.tensor_meta.dtype,
    )
    return OutputSharding(
        DTensorSpec.from_dim_map(
            input_spec.mesh,
            output_dim_map,
            pending_sums,
            tensor_meta=tensor_meta,
        )
    )