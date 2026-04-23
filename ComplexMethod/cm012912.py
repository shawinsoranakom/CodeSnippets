def _lower_quantized_binary_op(model: GraphModule, qconfig_map: dict[str, QConfigAny]):
    binary_ops_to_lower: list[Callable] = [
        operator.add,
        torch.add,
        operator.mul,
        torch.mul,
        torch.matmul,
    ]
    modules = dict(model.named_modules(remove_duplicate=False))
    for n in model.graph.nodes:
        # Step 0: Find nodes that match this pattern (dequantize - ref module - quantize)
        (q_node, relu_node, bop_node) = _match_static_pattern(
            n,
            modules,
            qconfig_map,
            binary_ops_to_lower,
            dequantize_node_arg_indices=[0, 1],
        )
        if q_node is None:
            continue
        if bop_node is None:
            raise AssertionError(
                "Expected a binary op node when matching quantized binary op pattern"
            )
        (_, scale_node, zero_point_node, _) = q_node.args

        # Step 1: Remove dequant nodes
        num_dq_nodes = 0
        for arg in bop_node.args:
            if not is_dequantize_node(arg):
                continue
            dq_node = arg
            if not isinstance(dq_node, Node):
                raise AssertionError("Expected dq_node to be a Node")
            dn_input = dq_node.args[0]
            bop_node.replace_input_with(dq_node, dn_input)  # type: ignore[arg-type]
            num_dq_nodes += 1
        if num_dq_nodes <= 0:
            raise AssertionError(
                "Expected at least one dequantize node in binary op args"
            )

        # Step 2: Swap binary op to quantized binary op
        if bop_node.target not in QBIN_OP_MAPPING:
            raise AssertionError(
                f"Unsupported binary op {bop_node.target} for lowering"
            )
        binop_to_qbinop = QBIN_OP_MAPPING if relu_node is None else QBIN_RELU_OP_MAPPING
        qbin_op = binop_to_qbinop[bop_node.target]
        # prepare the args for quantized binary op
        # (x, y)
        qop_node_args = list(bop_node.args)
        # (x, y, scale, zero_point)
        # add scale and zero_point arguments for Tensor - Tensor operation
        if num_dq_nodes == 2:
            qop_node_args.extend([scale_node, zero_point_node])
        # insert a call to quantized binary op and remove the original binary op
        with model.graph.inserting_after(q_node):
            qop_node = create_node_from_old_node_preserve_meta(
                model.graph,
                ("call_function", qbin_op, tuple(qop_node_args), {}),
                bop_node,
            )
            q_node.replace_all_uses_with(qop_node)

        # Step 3: Remove quantize node, binary op node, and relu node if any
        model.graph.erase_node(q_node)
        if relu_node is not None:
            model.graph.erase_node(relu_node)
        model.graph.erase_node(bop_node)