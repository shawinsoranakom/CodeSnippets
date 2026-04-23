def prim_loop(g: jit_utils.GraphContext, *inputs, **attrs) -> list[_C.Value]:
    node = g.original_node
    env = g.env
    values_in_env = g.values_in_env
    params_dict = g.params_dict

    operator_export_type = GLOBALS.operator_export_type
    opset_version = GLOBALS.export_onnx_opset_version

    old_blocks = tuple(node.blocks())
    _new_op_outputs, new_block_contexts, new_node = jit_utils.add_op_with_blocks(
        g, "Loop", *inputs, outputs=node.outputsSize(), n_blocks=len(old_blocks)
    )

    for old_block, new_block_context in zip(old_blocks, new_block_contexts):
        # Copy input metadata to subblock
        #
        #   prim::Loop(iter, cond, input_1, ..., input_n)
        #     block0(iter, input_1, ..., input_n)
        #
        # For `Loop` node, copy metadata for `iter`, `input_1`, ..., `input_n`.
        for i, b_in in enumerate(old_block.inputs()):
            if i == 0 and i < len(inputs):
                b_in.setType(inputs[i].type())
            # For optional block inputs, they may switch between None not-None inside
            # the loop body, so if the loop input is not optional, the block input may
            # still need to be optional.
            if (
                i > 0
                and (i + 1) < len(inputs)
                and not isinstance(b_in.type(), _C.OptionalType)
            ):
                b_in.setType(inputs[i + 1].type())
        torch._C._jit_pass_onnx_block(
            old_block,
            new_block_context.block,
            operator_export_type,
            env,
            values_in_env,
            False,
        )
    fixed_outputs = torch._C._jit_pass_fixup_onnx_controlflow_node(
        new_node, opset_version
    )
    # Run shape type inference for Loop after subblock is converted.
    if GLOBALS.onnx_shape_inference:
        torch._C._jit_pass_onnx_node_shape_type_inference(
            new_node, params_dict, opset_version
        )
    return fixed_outputs