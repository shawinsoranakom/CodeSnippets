def _lower_static_weighted_ref_module_with_two_inputs(
    model: GraphModule, qconfig_map: dict[str, QConfigAny]
):
    """
    Traverse the graph and find patterns
    dequantize   dequantize
       \\         //
        ref module
            \\
          quantize
    and replace them with the quantized version of the ref module.
    """
    modules = dict(model.named_modules(remove_duplicate=False))
    for n in model.graph.nodes:
        #                                            (dequantize \
        # Step 0: Find nodes that match this pattern (dequantize - ref module - quantize)
        matching_modules = list(STATIC_LOWER_FUSED_MODULE_TWO_INPUTS_MAP.keys())
        (q_node, ref_node) = _match_static_pattern_with_two_inputs(
            n,
            modules,
            qconfig_map,
            matching_modules,  # type: ignore[arg-type]
        )
        if q_node is None:
            continue
        if ref_node is None:
            raise AssertionError(
                "Expected a reference node when matching static pattern with two inputs"
            )
        (_, scale_node, zero_point_node, _) = q_node.args
        ref_module = _get_module(ref_node, modules)
        ref_class = type(ref_module)
        if not isinstance(scale_node, Node):
            raise AssertionError("Expected scale_node to be a Node")
        if not isinstance(zero_point_node, Node):
            raise AssertionError("Expected zero_point_node to be a Node")
        if not issubclass(ref_class, nn.Module):
            raise AssertionError(
                "Expected reference module class to be a subclass of nn.Module"
            )

        # Step 1: Change this pattern to use the corresponding quantized module
        # For fused modules, we also check whether the inner module is a reference module
        # If so, we replace the entire fused module with the corresponding quantized module
        if ref_class in STATIC_LOWER_FUSED_MODULE_TWO_INPUTS_MAP:
            inner_ref_class, q_class = STATIC_LOWER_FUSED_MODULE_TWO_INPUTS_MAP[
                ref_class
            ]
            if type(ref_module[0]) is not inner_ref_class:  # type: ignore[index]
                continue
        else:
            continue
        output_scale = getattr(model, scale_node.target)  # type: ignore[arg-type]
        output_zero_point = getattr(model, zero_point_node.target)  # type: ignore[arg-type]
        q_module = q_class.from_reference(ref_module, output_scale, output_zero_point)
        # replace reference module with quantized module
        parent_name, module_name = _parent_name(ref_node.target)
        setattr(modules[parent_name], module_name, q_module)

        # Step 2: Reroute around dq_node, and remove q_node and its args
        if len(ref_node.args) != 2:
            raise AssertionError("Expected reference node to have exactly 2 args")
        for arg in ref_node.args:
            if not is_dequantize_node(arg):
                continue
            dq_node = arg
            if not isinstance(dq_node, Node):
                raise AssertionError("Expected dq_node to be a Node")
            ref_node.replace_input_with(dq_node, dq_node.args[0])  # type: ignore[arg-type]

        q_node.replace_all_uses_with(ref_node)
        model.graph.erase_node(q_node)
        model.graph.erase_node(scale_node)
        model.graph.erase_node(zero_point_node)