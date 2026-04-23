def _lower_dynamic_weighted_ref_functional(
    model: GraphModule, qconfig_map: dict[str, QConfigAny]
):
    """
    Traverse the graph and replace functional reference patterns with their dynamically
    quantized versions.
    Examples:
    quantize_per_tensor_dynamic - dequantize - functional linear --> linear_dynamic
    to(torch.float16) - dequantize - functional linear --> linear_dynamic_fp16
    """
    modules = dict(model.named_modules(remove_duplicate=False))
    # we want to search in reserved order so that we can match the larger patterns first
    # e.g. we want to match linear - relu before linear.
    for n in reversed(model.graph.nodes):
        # Step 0: Find nodes that match this pattern
        # (quantize_per_tensor_dynamic - dequantize - dynamically quantized op)
        # We search for the pattern backwards, starting with the quantize node
        # Quantize node args: (func, scale, zp, dtype)
        func_node = n
        # Handle cases where the functional op is wrapped in a ReLU
        if (
            func_node.op == "call_function"
            and func_node.target is F.relu
            or func_node.op == "call_module"
            and type(modules[str(func_node.target)]) is torch.nn.ReLU
        ):
            relu_node = func_node
            func_node = relu_node.args[0]
        else:
            relu_node = None
        if should_skip_lowering(func_node, qconfig_map):
            continue
        # Linear args: (dequantized inputs, dequantized weights[, bias])
        # Conv args: (dequantized inputs, dequantized weights[, bias, stride, padding, dilation, groups])
        if (
            func_node.op != "call_function"
            or func_node.target not in DYNAMIC_LOWER_FUNCTIONAL_MAP
        ):
            continue
        (input_dq_node, weight_dq_node, *remaining_func_args) = func_node.args
        if (
            input_dq_node.op != "call_method"
            or input_dq_node.target != "dequantize"
            or weight_dq_node.op != "call_method"
            or weight_dq_node.target != "dequantize"
        ):
            continue

        input_dynamic_q_node = input_dq_node.args[0]

        if (
            input_dynamic_q_node.op != "call_function"
            or input_dynamic_q_node.target != torch.quantize_per_tensor_dynamic
        ):
            continue

        reduce_range_node = None
        (pattern_input, activation_dtype, reduce_range_node) = input_dynamic_q_node.args
        is_fp16 = activation_dtype == torch.float16
        is_int8 = activation_dtype in [torch.quint8, torch.qint8]
        if not is_int8 and not is_fp16:
            continue

        quantized_weight = weight_dq_node.args[0]
        weight_dtype = quantized_weight.args[-1]

        # Step 1: Try to select reference pattern with the corresponding quantized op
        dynamic_quant_dtype_key = (activation_dtype, weight_dtype)
        if (
            dynamic_quant_dtype_key
            not in DYNAMIC_LOWER_FUNCTIONAL_MAP[func_node.target]
        ):
            print(
                f"Didn't find dtype combination {dynamic_quant_dtype_key} during "
                f"dynamic quantized op lowering for {func_node.target}"
            )
            continue
        (q_func, q_relu_func) = DYNAMIC_LOWER_FUNCTIONAL_MAP[func_node.target][
            dynamic_quant_dtype_key
        ]

        if q_func is None or q_relu_func is None:
            print(
                "Didn't find corresponding quantized function or quantized relu function "
                f"for {func_node.target}, {dynamic_quant_dtype_key}"
            )
            continue

        # Step 2: Replace quantized weights with packed weights, which will be folded later
        # Use the right prepack op and prepare the corresponding args
        # Linear prepack args: (quantized weights[, bias])
        # Conv prepack args: (quantized weights[, bias, stride, padding, dilation, groups])
        prepack_args: list[Any] = [quantized_weight] + remaining_func_args
        prepack_kwargs = {}
        if func_node.target is F.linear:
            prepack_op = get_linear_prepack_op_for_dtype(weight_dtype)
            kwargs = func_node.kwargs.copy()
            if "bias" in kwargs:
                prepack_kwargs["B"] = kwargs["bias"]
                del kwargs["bias"]
                func_node.kwargs = kwargs
        elif func_node.target in CONV_FUNCTIONAL_OPS:
            prepack_op = get_qconv_prepack_op(func_node.target)
            # For conv1d, the stride, padding, and dilation args may be ints,
            # in which case we need to convert them to tuples
            if func_node.target is F.conv1d:
                for i in [2, 3, 4]:
                    if len(prepack_args) > i and isinstance(prepack_args[i], int):
                        prepack_args[i] = (prepack_args[i],)
        else:
            raise ValueError(f"Lowering is not supported for op '{func_node.target}'")
        with model.graph.inserting_before(func_node):
            packed_weight = model.graph.create_node(
                "call_function", prepack_op, tuple(prepack_args), prepack_kwargs
            )

        # Step 3: Replace reference pattern with the corresponding quantized op
        func_node.target = q_relu_func if relu_node is not None else q_func
        if is_int8:
            func_node.args = (pattern_input, packed_weight, reduce_range_node)
        else:
            func_node.args = (pattern_input, packed_weight)

        if relu_node is not None:
            relu_node.replace_all_uses_with(func_node)

        # Step 4: Remove the relu node if it exists
        if relu_node is not None:
            model.graph.erase_node(relu_node)