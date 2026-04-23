def group_norm(
    g: jit_utils.GraphContext, input, num_groups, weight, bias, eps, cudnn_enabled
):
    channel_size = symbolic_helper._get_tensor_dim_size(input, 1)
    if channel_size is not None:
        if channel_size % num_groups != 0:
            raise AssertionError(
                f"channel_size ({channel_size}) must be divisible by num_groups ({num_groups})"
            )
    input_rank = symbolic_helper._get_tensor_rank(input)
    if input_rank is None:
        return symbolic_helper._unimplemented("group_norm", "unknown input rank", input)
    # 0 in the shape list keeps dimension value unchanged.
    shape = [0, num_groups, -1]
    input_reshaped = symbolic_helper._reshape_helper(
        g, input, g.op("Constant", value_t=torch.LongTensor(shape))
    )

    # C is always divisible by num_groups
    # Due to shape difference. we need to apply weight and bias after
    # instance norm computation and reshape
    weight_ = g.op(
        "Constant",
        value_t=torch.tensor(
            [1.0] * num_groups,
            dtype=_type_utils.JitScalarType.from_value(input).dtype(),
        ),
    )
    bias_ = g.op(
        "Constant",
        value_t=torch.tensor(
            [0.0] * num_groups,
            dtype=_type_utils.JitScalarType.from_value(input).dtype(),
        ),
    )

    norm_reshaped = g.op(
        "InstanceNormalization", input_reshaped, weight_, bias_, epsilon_f=eps
    )
    norm = symbolic_helper._reshape_helper(g, norm_reshaped, g.op("Shape", input))

    if weight is None or weight.node().mustBeNone():
        weight_value = torch.tensor(
            [1.0], dtype=_type_utils.JitScalarType.from_value(input).dtype()
        )
        weight = g.op("Constant", value_t=weight_value)
    if bias is None or bias.node().mustBeNone():
        bias_value = torch.tensor(
            [0.0], dtype=_type_utils.JitScalarType.from_value(input).dtype()
        )
        bias = g.op("Constant", value_t=bias_value)

    # Norm has shape [N, C, *] so we reshape weight and bias to [C, *]
    axes = list(range(1, input_rank - 1))
    return add(
        g,
        mul(g, norm, symbolic_helper._unsqueeze_helper(g, weight, axes)),
        symbolic_helper._unsqueeze_helper(g, bias, axes),
    )