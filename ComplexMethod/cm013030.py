def scaled_dot_product_attention(
    g: jit_utils.GraphContext,
    query: torch._C.Value,
    key: torch._C.Value,
    value: torch._C.Value,
    attn_mask: torch._C.Value | None = None,
    dropout_p: float = 0.0,
    is_causal: bool = False,
    scale: torch._C.Value | None = None,
    enable_gqa: bool = False,
):
    if is_causal and not symbolic_helper._is_none(attn_mask):
        raise AssertionError("is_causal and attn_mask cannot be set at the same time")
    if enable_gqa:
        raise AssertionError(
            "conversion of scaled_dot_product_attention not implemented if enable_gqa is True"
        )

    if symbolic_helper._is_none(scale):
        scale = _attention_scale(g, query)

    if is_causal:
        attn_mask = _causal_attention_mask(g, query, key)

    # Swap the last two axes of key
    # NOTE: onnx-script has different logic here, because the attribute perms in
    # transpose needs list of ints
    key_shape_builtin = symbolic_helper._get_tensor_rank(key)
    # pyrefly: ignore [bad-argument-type, no-matching-overload]
    key_transposed_axes = list(range(key_shape_builtin))
    key_transposed_axes[-1], key_transposed_axes[-2] = (
        key_transposed_axes[-2],
        key_transposed_axes[-1],
    )
    key_transposed = g.op("Transpose", key, perm_i=key_transposed_axes)

    # https://github.com/pytorch/pytorch/blob/12da0c70378b5be9135c6fda62a9863bce4a4818/aten/src/ATen/native/transformers/attention.cpp#L653
    # Scale q, k before matmul for stability see https://tinyurl.com/sudb9s96 for math
    # pyrefly: ignore [bad-argument-type]
    query_scaled = g.op("Mul", query, g.op("Sqrt", scale))
    # pyrefly: ignore [bad-argument-type]
    key_transposed_scaled = g.op("Mul", key_transposed, g.op("Sqrt", scale))
    mul_qk = g.op("MatMul", query_scaled, key_transposed_scaled)

    if symbolic_helper._is_none(attn_mask):
        mul_qk_add = mul_qk
        attn_weight = g.op("Softmax", mul_qk_add, axis_i=-1)
    elif (
        _type_utils.JitScalarType.from_value(attn_mask)
        == _type_utils.JitScalarType.BOOL
    ):
        # Turn the Boolean mask to float: attn_mask.masked_fill(not attn_mask, -float('inf'))
        const_zero = g.op("Constant", value_t=torch.tensor([0.0]))
        const_neg_inf = g.op("Constant", value_t=torch.tensor([-float("inf")]))
        # pyrefly: ignore [bad-argument-type]
        attn_mask = g.op("Where", attn_mask, const_zero, const_neg_inf)
        mul_qk_add = g.op("Add", mul_qk, attn_mask)
        attn_weight = g.op("Softmax", mul_qk_add, axis_i=-1)
        # When using scaled dot product attention with a boolean mask, the softmax operation might return NaN values
        # due to the presence of -inf in an entire row (padding tokens), resulting in 0/0 (NaN) in the softmax output.
        # This is because there's no safe softmax imp in ONNX, so we need to handle NaN values explicitly to match
        # the behavior of PyTorch with boolean masks.
        attn_weight = g.op("Where", g.op("IsNaN", attn_weight), const_zero, attn_weight)
    elif _type_utils.JitScalarType.from_value(attn_mask) in (
        _type_utils.JitScalarType.FLOAT,
        _type_utils.JitScalarType.HALF,
        _type_utils.JitScalarType.BFLOAT16,
    ):
        # pyrefly: ignore [bad-argument-type]
        mul_qk_add = g.op("Add", mul_qk, attn_mask)
        attn_weight = g.op("Softmax", mul_qk_add, axis_i=-1)
    else:
        raise ValueError(
            f"Unsupported type for attn_mask: {_type_utils.JitScalarType.from_value(attn_mask)}"
        )

    if dropout_p != 0:
        attn_weight = g.op(
            "Dropout",
            attn_weight,
            g.op("Constant", value_t=torch.tensor(dropout_p, dtype=torch.float)),
        )

    return g.op("MatMul", attn_weight, value)