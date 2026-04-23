def _verify_exported_program_signature(exported_program) -> None:
    # Check ExportedProgram signature matches
    gs = exported_program.graph_signature

    # Check every node in the signature exists in the graph
    input_node_names = [
        node.name for node in exported_program.graph.nodes if node.op == "placeholder"
    ]

    if len(input_node_names) != len(gs.input_specs):
        input_spec_names = [
            spec.arg.name for spec in gs.input_specs if hasattr(spec.arg, "name")
        ]
        missing_in_specs = set(input_node_names) - set(input_spec_names)
        missing_in_graph = set(input_spec_names) - set(input_node_names)
        raise SpecViolationError(
            f"Number of graph inputs ({len(input_node_names)}) "
            f"does not match number of inputs in the graph signature ({len(gs.input_specs)})\n"
            f"Placeholders missing input_specs: {missing_in_specs}\n"
            f"Input_specs missing placeholders: {missing_in_graph}"
        )

    for input_spec, node in zip(gs.input_specs, input_node_names):
        if isinstance(
            input_spec.arg,
            (TensorArgument, SymIntArgument, SymFloatArgument, SymBoolArgument),
        ):
            if input_spec.arg.name != node:
                raise SpecViolationError(
                    f"Input spec name {input_spec.arg.name} does not match node name {node}"
                )

        if input_spec.kind == InputKind.USER_INPUT:
            continue

        elif input_spec.kind == InputKind.PARAMETER:
            if not isinstance(input_spec.arg, TensorArgument):
                raise SpecViolationError(
                    f"Parameter {input_spec.name} is not a tensor argument. Found {input_spec.arg} instead."
                )
            if input_spec.target is None:
                raise SpecViolationError(
                    f"InputSpec for {input_spec.name} has no target."
                )

            param = input_spec.target
            if param not in exported_program.state_dict:
                raise SpecViolationError(f"Parameter {param} is not in the state dict.")

            if not isinstance(exported_program.state_dict[param], torch.nn.Parameter):
                raise SpecViolationError(
                    f"State dict entry for parameter {param} is not an instance of torch.nn.Parameter."
                )

        elif input_spec.kind == InputKind.BUFFER:
            if not isinstance(input_spec.arg, TensorArgument):
                raise SpecViolationError(
                    f"Buffer {input_spec.name} is not a tensor argument. Found {input_spec.arg} instead."
                )
            if input_spec.target is None:
                raise SpecViolationError(
                    f"InputSpec for {input_spec.name} has no target."
                )

            buffer = input_spec.target
            if input_spec.persistent is None:
                raise SpecViolationError(
                    f"Buffer {buffer} is missing a persistence flag"
                )

            if (
                input_spec.persistent is True
                and buffer not in exported_program.state_dict
            ):
                raise SpecViolationError(f"Buffer {buffer} is not in the state dict.")

            if input_spec.persistent is False and buffer in exported_program.state_dict:
                raise SpecViolationError(
                    f"Non-persistent buffer {buffer} is in the state dict, it should not be."
                )
        elif input_spec.kind == InputKind.CONSTANT_TENSOR:
            if not isinstance(input_spec.arg, TensorArgument):
                raise SpecViolationError(
                    f"Constant tensor {input_spec.name} is not a tensor argument. Found {input_spec.arg} instead."
                )
            if input_spec.target is None:
                raise SpecViolationError(
                    f"InputSpec for {input_spec.name} has no target."
                )

            tensor_const = input_spec.target
            if tensor_const not in exported_program.constants:
                raise SpecViolationError(
                    f"Constant tensor {tensor_const} is not in the constants dictionary."
                )
        elif input_spec.kind == InputKind.CUSTOM_OBJ:
            if not isinstance(input_spec.arg, CustomObjArgument):
                raise SpecViolationError(
                    f"Custom object {input_spec.name} is not a custom object argument. Found {input_spec.arg} instead."
                )
            if input_spec.target is None:
                raise SpecViolationError(
                    f"InputSpec for {input_spec.name} has no target."
                )

            custom_obj = input_spec.target
            if custom_obj not in exported_program.constants:
                raise SpecViolationError(
                    f"Custom object {custom_obj} is not in the constants dictionary."
                )
        elif input_spec.kind == InputKind.TOKEN:
            if not isinstance(input_spec.arg, TokenArgument):
                raise SpecViolationError(
                    f"Constant tensor {input_spec.name} is not a tensor argument. Found {input_spec.arg} instead."
                )
        else:
            raise SpecViolationError(f"Unknown InputKind {input_spec.kind}.")

    # Check outputs
    output_node = list(exported_program.graph.nodes)[-1]
    if output_node.op != "output":
        raise AssertionError(f"last node must be output, got {output_node.op}")
    output_nodes = [
        arg.name if isinstance(arg, torch.fx.Node) else arg
        for arg in output_node.args[0]
    ]

    if len(output_nodes) != len(gs.output_specs):
        output_spec_names = [
            spec.arg.name if hasattr(spec.arg, "name") else str(spec.arg)
            for spec in gs.output_specs
        ]
        missing_out_specs = set(output_nodes) - set(output_spec_names)
        missing_out_graph = set(output_spec_names) - set(output_nodes)
        raise SpecViolationError(
            f"Number of output nodes {len(output_nodes)} is different "
            f"Than the number of outputs specified by the graph signature: {len(gs.output_specs)}\n"
            f"Nodes missing output_specs: {missing_out_specs}\n"
            f"Output_specs missing nodes: {missing_out_graph}"
        )

    num_tokens = len(gs.output_tokens)
    end = (
        len(gs.buffers_to_mutate)
        + len(gs.parameters_to_mutate)
        + len(gs.user_inputs_to_mutate)
        + num_tokens
    )
    mutate_nodes: list[str] = output_nodes[num_tokens:end]
    user_output_nodes = output_nodes[end : end + len(gs.user_outputs)]

    for mutation_node in mutate_nodes:
        if mutation_node in gs.buffers_to_mutate:
            if gs.buffers_to_mutate[mutation_node] not in gs.buffers:
                raise SpecViolationError(
                    f"Buffer output {mutation_node} does not point to a buffer that exists. \n"
                    f"Dict of buffers that are mutated, in order: {gs.buffers_to_mutate} \n"
                    f"Buffer nodes available: {gs.buffers} \n"
                )
        elif mutation_node in gs.parameters_to_mutate:
            if gs.parameters_to_mutate[mutation_node] not in gs.parameters:
                raise SpecViolationError(
                    f"Parameter output {mutation_node} does not point to a parameter that exists. \n"
                    f"Dict of parameters that are mutated, in order: {gs.parameters_to_mutate} \n"
                    f"Parameter nodes available: {gs.parameters} \n"
                )
        elif mutation_node in gs.user_inputs_to_mutate:
            if gs.user_inputs_to_mutate[mutation_node] not in gs.user_inputs:
                raise SpecViolationError(
                    f"User input output {mutation_node} does not point to a user input that exists. \n"
                    f"Dict of user inputs that are mutated, in order: {gs.user_inputs_to_mutate} \n"
                    f"User input nodes available: {gs.user_inputs} \n"
                )
        else:
            raise SpecViolationError(
                f"Mutation node {mutation_node} is neither a buffer nor a user input. "
                f"Buffers to mutate: {gs.buffers_to_mutate}, User inputs to mutate: {gs.user_inputs_to_mutate}"
            )

    for user_output_node, user_output_name in zip(user_output_nodes, gs.user_outputs):
        if user_output_node != user_output_name:
            raise SpecViolationError(
                f"User output {user_output_node} is not in the correct "
                "order or is not found in the "
                f"exported program's user_output list: {gs.user_outputs}. "
            )