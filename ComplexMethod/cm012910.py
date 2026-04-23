def _lower_static_weighted_ref_functional(
    model: GraphModule, qconfig_map: dict[str, QConfigAny]
):
    """
    Traverse the graph and replace functional reference patterns with their quantized versions.
    """
    modules = dict(model.named_modules(remove_duplicate=False))
    for n in model.graph.nodes:
        # Step 0: Find nodes that match this pattern (dequantize - functional op - quantize)
        matching_ops = list(STATIC_LOWER_FUNCTIONAL_MAP.keys())
        (q_node, relu_node, func_node) = _match_static_pattern(
            n, modules, qconfig_map, matching_ops, dequantize_node_arg_indices=[0, 1]
        )
        if q_node is None:
            continue
        if func_node is None:
            raise AssertionError(
                "Expected a function node when matching static functional pattern"
            )
        (_, output_scale_node, output_zp_node, _) = q_node.args
        (input_dq_node, weight_dq_node, *remaining_func_args) = func_node.args
        if not isinstance(output_zp_node, Node):
            raise AssertionError("Expected output_zp_node to be a Node")
        if not isinstance(input_dq_node, Node):
            raise AssertionError("Expected input_dq_node to be a Node")
        if not isinstance(weight_dq_node, Node):
            raise AssertionError("Expected weight_dq_node to be a Node")
        quantized_weight = weight_dq_node.args[0]
        if not isinstance(quantized_weight, Node):
            raise AssertionError("Expected quantized_weight to be a Node")
        if quantized_weight.op != "call_function" or quantized_weight.target not in (
            torch.quantize_per_tensor,
            torch.quantize_per_channel,
        ):
            continue

        # Step 1: Replace quantized weights with packed weights, which will be folded later
        # Use the right prepack op and prepare the corresponding args
        # Linear prepack args: (quantized weights[, bias])
        # Conv prepack args: (quantized weights[, bias, stride, padding, dilation, groups])
        prepack_args: list[Any] = [quantized_weight] + remaining_func_args
        if func_node.target is F.linear:
            weight_dtype = quantized_weight.args[-1]
            prepack_op = get_linear_prepack_op_for_dtype(weight_dtype)
        elif func_node.target in CONV_FUNCTIONAL_OPS:
            prepack_op = get_qconv_prepack_op(func_node.target)  # type: ignore[arg-type]
            # For conv1d, the stride, padding, and dilation args may be ints,
            # in which case we need to convert them to tuples
            if func_node.target is F.conv1d:
                for i in [2, 3, 4]:
                    if len(prepack_args) > i and isinstance(prepack_args[i], int):
                        prepack_args[i] = (prepack_args[i],)
        elif func_node.target in CONV_TRANSPOSE_FUNCTIONAL_OPS:
            prepack_op = get_qconv_prepack_op(func_node.target)  # type: ignore[arg-type]
            # For conv_transpose1d, the stride, padding, and dilation args may be ints,
            # in which case we need to convert them to tuples
            if func_node.target is F.conv_transpose1d:
                # Note prepack_args[5] is groups.
                for i in [2, 3, 4, 6]:
                    if len(prepack_args) > i and isinstance(prepack_args[i], int):
                        prepack_args[i] = (prepack_args[i],)
            # swap dilation and groups
            # prepack op has arguments: {w, b, stride, padding, output_padding, dilation, groups}
            # transposed conv op has arguments: {x, w, b, stride, padding, output_padding, groups, dilation}
            if len(prepack_args) > 6:
                prepack_args[5], prepack_args[6] = prepack_args[6], prepack_args[5]
        else:
            raise ValueError(f"Lowering is not supported for op '{func_node.target}'")
        with model.graph.inserting_before(output_scale_node):  # type: ignore[arg-type]
            # kwargs of the func node are needed for prepack op (i.e., quantized::linear_prepack)
            # They are not needed for compute op (i.e., quantized::linear)
            kwargs = func_node.kwargs
            # F.linear uses 'bias' key for bias while qlinear_prepack uses 'B' for bias
            if func_node.target is F.linear and "bias" in kwargs:
                kwargs = kwargs.copy()
                kwargs["B"] = kwargs["bias"]
                del kwargs["bias"]
            packed_weight = model.graph.create_node(
                "call_function", prepack_op, tuple(prepack_args), kwargs
            )

        # Step 2: Replace reference pattern with the corresponding quantized op
        (q_func, q_relu_func) = STATIC_LOWER_FUNCTIONAL_MAP[func_node.target]  # type: ignore[index]
        # conv_transpose does not support fusion with relu yet. q_relu_func is None in such cases
        if q_relu_func is not None:
            func_node.target = q_relu_func if relu_node is not None else q_func
        else:
            func_node.target = q_func
        func_node.args = (
            input_dq_node.args[0],
            packed_weight,
            output_scale_node,
            output_zp_node,
        )
        # kwargs for func_node has been moved to kwargs for prepack op
        func_node.kwargs = {}
        q_node.replace_all_uses_with(func_node)
        # Move func_node after output_zp_node in the graph
        output_zp_node.append(func_node)

        # Clean up: Remove quantize node, and the relu node if it exists
        model.graph.erase_node(q_node)
        if relu_node is not None and q_relu_func is not None:
            model.graph.erase_node(relu_node)