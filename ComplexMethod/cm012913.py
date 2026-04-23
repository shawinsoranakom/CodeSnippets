def special_pattern_replacement(model: GraphModule):
    modules = dict(model.named_modules(remove_duplicate=False))
    for n in model.graph.nodes:
        q_node = n
        is_quantize = q_node.target is torch.quantize_per_tensor
        is_to_fp16 = (
            q_node.op == "call_method"
            and q_node.target == "to"
            and len(q_node.args) == 2
            and q_node.args[1] == torch.float16
        )
        # Only continue when neither quantize nor to_fp16
        if not is_quantize and not is_to_fp16:
            continue
        ref_node = q_node.args[0]
        # get output scale/zero_point/dtype from the quantize node
        # ref_node, scale_node, zero_point_node, dtype = q_node.args
        # TODO: add safety checks that users for the ref_node and dq_node needs to be one
        is_call_function, is_call_method, is_call_module = is_fixed_qparams_node(
            ref_node, modules
        )
        if is_to_fp16 and (is_call_function or is_call_method or is_call_module):
            # TODO: add a warning or error out here? (bc-breaking if error out)
            # warnings.warn(
            #     "Only reference patterns are currently supported for {dtype} dtype with {op} op"
            #     "".format(dtype=dtypes, op=ref_node))
            continue

        is_call_function, is_call_method, is_call_module = is_default_node(
            ref_node, modules
        )
        if is_to_fp16 and (is_call_function or is_call_method or is_call_module):
            # TODO: add a warning or error out here? (bc-breaking if error out)
            continue

        # This check includes all supported ops
        is_call_function, is_call_method, is_call_module = is_special_pattern_node(
            ref_node, modules
        )
        if not (is_call_module or is_call_function or is_call_method):
            continue
        if len(ref_node.args) <= 0 and len(ref_node.kwargs) <= 0:
            raise AssertionError("Expected ref_node to have args or kwargs")
        dq_node_or_nodes = (
            ref_node.args[0]
            if len(ref_node.args) > 0
            else next(iter(ref_node.kwargs.values()))
        )
        if not isinstance(dq_node_or_nodes, (Node, tuple, list)):
            raise AssertionError(
                "Expected dq_node_or_nodes to be a Node, tuple, or list"
            )
        is_dequantize = False
        if isinstance(dq_node_or_nodes, Node):
            is_dequantize = (
                dq_node_or_nodes.op == "call_method"
                and dq_node_or_nodes.target == "dequantize"
            )
        elif isinstance(dq_node_or_nodes, (tuple, list)):
            is_dequantize = all(
                x.op == "call_method" and x.target == "dequantize"
                for x in dq_node_or_nodes
            )

        if not is_dequantize:
            continue

        # TODO: enable we have patterns that needs to swap the modules
        if is_call_module:
            ref_module = modules[ref_node.target]
            if type(ref_module) in SPECIAL_PATTERN_LOWER_MODULE_MAP and is_quantize:
                qmodule_cls = SPECIAL_PATTERN_LOWER_MODULE_MAP.get(type(ref_module))
                scale_node = q_node.args[1]
                zero_point_node = q_node.args[2]
                output_scale = getattr(model, scale_node.target)
                output_zero_point = getattr(model, zero_point_node.target)

                qmodule = qmodule_cls.from_reference(  # type:ignore[union-attr]
                    ref_module, output_scale, output_zero_point
                )
                # replace reference module with quantized module
                parent_name, module_name = _parent_name(ref_node.target)
                setattr(modules[parent_name], module_name, qmodule)

        # reroute around dq node:
        dq_nodes: list[Node] = []
        if isinstance(dq_node_or_nodes, Node):
            dq_nodes = [dq_node_or_nodes]
        elif isinstance(dq_node_or_nodes, (tuple, list)):
            dq_nodes = list(dq_node_or_nodes)

        for dq_node in dq_nodes:
            dn_input = dq_node.args[0]
            ref_node.replace_input_with(dq_node, dn_input)

        # store q node args
        qnode_qparams = list(q_node.args)[1:]
        # replace uses of q node with input and remove q node
        q_node_input = q_node.args[0]
        q_node.replace_all_uses_with(q_node_input)
        model.graph.erase_node(q_node)

        is_call_function, is_call_method, is_call_module = is_default_node(
            ref_node, modules
        )
        if is_call_function:
            # pass scale/zer_point arguments from quantize_per_tensor to the default node operator
            # insert an op after the zero_point node so that the scale/zero_point
            # nodes are is available
            qop = get_quantized_operator(ref_node.target)
            args = list(ref_node.args)
            kwargs = dict(ref_node.kwargs)
            if qop in QOP_TO_ARG_NAMES_TO_SKIP:
                args_to_skip = QOP_TO_ARG_NAMES_TO_SKIP[qop]
                for arg in args_to_skip:
                    if arg in kwargs:
                        kwargs.pop(arg)
            kwargs["output_scale"] = qnode_qparams[0]
            kwargs["output_zero_point"] = qnode_qparams[1]
            with model.graph.inserting_after(qnode_qparams[1]):
                qop_node = create_node_from_old_node_preserve_meta(
                    model.graph, ("call_function", qop, tuple(args), kwargs), ref_node
                )
                ref_node.replace_all_uses_with(qop_node)
                model.graph.erase_node(ref_node)
        else:
            # remove scale/zero_point node for quantize node
            for n in qnode_qparams:
                if isinstance(n, Node):
                    model.graph.erase_node(n)

    return model