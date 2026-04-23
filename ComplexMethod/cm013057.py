def prim_if(g: jit_utils.GraphContext, *inputs, **attrs) -> list[_C.Value]:
    n = g.original_node
    block = g.block
    env = g.env
    values_in_env = g.values_in_env
    params_dict = g.params_dict

    operator_export_type = GLOBALS.operator_export_type
    opset_version = GLOBALS.export_onnx_opset_version

    static_if = inputs[0].node().kind() == "onnx::Constant"
    if static_if:
        # Fold static if
        #
        # The torch IR
        # graph(%embedding_matrix.1 : Float(10, 15, strides=[15, 1], requires_grad=0, device=cpu),
        #    %input.1 : Long(6, strides=[1], requires_grad=0, device=cpu), ...
        # %65 : Bool(requires_grad=0, device=cpu) = prim::Constant[value={0}]()
        # %21 : Long(device=cpu) = aten::eq(%20, %64)
        # %22 : Long(device=cpu) = prim::If(%21)
        #     block0():
        #     %23 : Long(device=cpu) = aten::is_floating_point(%input.1)
        #     -> (%23)
        #     block1():
        #     -> (%65)
        # %input.53 : Tensor, %weight : Tensor = prim::If(%22)
        #     block0():
        #     -> (%embedding_matrix.1, %input.1)
        #     block1():
        #     -> (%input.1, %embedding_matrix.1)
        # %26 : int[] = aten::size(%input.53)
        #
        # The converted ONNX graph
        # %10 : Bool(device=cpu) = onnx::Constant[value={0}]()
        # %14 : Bool(device=cpu) = onnx::Equal(%13, %8)
        # %15 : Bool(requires_grad=0, device=cpu) = onnx::Constant[value={0}]()
        # %16 : Long(1, strides=[1], device=cpu) = onnx::Shape(%input.1)
        input_flag = symbolic_helper._node_get(inputs[0].node(), "value").tolist()
        const_value = (
            all(input_flag) if isinstance(input_flag, list) else bool(input_flag)
        )
        block_idx = 0 if const_value else 1
        current_b = list(n.blocks())[block_idx]
        env = torch._C._jit_pass_onnx_block(
            current_b,
            block,
            operator_export_type,
            env,
            values_in_env,
            True,
        )
        if_output_list = list(n.outputs())
        current_b_list = list(current_b.outputs())

        final_b_list = []
        for idx in range(len(if_output_list)):
            if current_b_list[idx] not in env:
                raise errors.SymbolicValueError(
                    f"The sub block ATen output {current_b_list[idx]} is not in env.",
                    current_b_list[idx],
                )  # type:ignore[operator]
            onnx_b = env[current_b_list[idx]]
            final_b_list.append(onnx_b)
        return final_b_list
    else:
        old_blocks = tuple(n.blocks())
        _new_op_outputs, new_block_contexts, new_node = jit_utils.add_op_with_blocks(
            g, "If", *inputs, outputs=n.outputsSize(), n_blocks=len(old_blocks)
        )

        for old_block, new_block_context in zip(old_blocks, new_block_contexts):
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
        # Run shape type inference for If after subblock is converted.
        if GLOBALS.onnx_shape_inference:
            torch._C._jit_pass_onnx_node_shape_type_inference(
                new_node, params_dict, opset_version
            )
        return fixed_outputs