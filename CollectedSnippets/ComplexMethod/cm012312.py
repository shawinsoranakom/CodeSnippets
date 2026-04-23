def _get_linear_dq_node(
    linear_node,
    input_index,
    input_dim_exceeds_two,
    input_contiguous,
    with_dtype_convert,
):
    act_reshape_node = None
    activation_to_bf16_node = None
    act_expand_node = None
    if input_dim_exceeds_two:
        if input_contiguous:
            act_reshape_node = linear_node.args[input_index]
            assert act_reshape_node.target is aten.reshape.default
            if not with_dtype_convert:
                # pattern: linear -> reshape -> dequant
                dequant_node = act_reshape_node.args[0]
            else:
                # pattern: linear -> reshape -> to_bf16 -> dequant
                activation_to_bf16_node = act_reshape_node.args[0]
                dequant_node = activation_to_bf16_node.args[0]
        else:
            # bmm pattern decomposed from linear when input dim exceeds 2 and not contiguous
            act_expand_node = linear_node.args[input_index]
            assert act_expand_node.target is aten.expand.default
            if not with_dtype_convert:
                dequant_node = act_expand_node.args[0]
            else:
                activation_to_bf16_node = act_expand_node.args[0]
                dequant_node = activation_to_bf16_node.args[0]
    else:
        if not with_dtype_convert:
            # pattern: linear -> dequant
            dequant_node = linear_node.args[input_index]
        else:
            # pattern: linear -> to_bf16 -> dequant
            activation_to_bf16_node = linear_node.args[input_index]
            dequant_node = activation_to_bf16_node.args[0]
    return dequant_node, act_reshape_node, activation_to_bf16_node, act_expand_node