def _unlift_exported_program_lifted_states(
    ep: ExportedProgram, check_guards=True
) -> torch.fx.GraphModule:
    check_guards = check_guards and _ok_to_generate_guards_fn()

    source_node_dict = {
        node.name: node for node in ep.graph.nodes if node.op != "placeholder"
    }
    # placeholder node name might change after deepcopy
    placeholder_source_node_dict = {
        node.target: node for node in ep.graph.nodes if node.op == "placeholder"
    }

    new_gm = torch.fx.GraphModule(ep.graph_module, copy.deepcopy(ep.graph))
    new_gm.meta.update(ep.graph_module.meta)
    ep = copy.copy(ep)
    ep._graph_signature = ExportGraphSignature(
        ep._graph_signature.input_specs, ep._graph_signature.output_specs
    )
    ep._graph_module = new_gm

    # TODO T206340015
    if ep.verifiers[0].dialect != "TRAINING":
        ep = _remove_effect_tokens(ep)

    _register_attrs_to_new_gm(new_gm, ep.graph_signature, ep.state_dict, ep.constants)
    forward_arg_names = (
        sig.forward_arg_names if (sig := ep.module_call_graph[0].signature) else None
    )
    lifted_inputs: list[str | None] = [
        (
            in_spec.target
            if in_spec.kind
            in (
                InputKind.BUFFER,
                InputKind.CONSTANT_TENSOR,
                InputKind.PARAMETER,
                InputKind.CUSTOM_OBJ,
            )
            else None
        )
        for in_spec in ep.graph_signature.input_specs
    ]

    mutated_outputs: list[str | None] = [
        (
            out_spec.target
            if out_spec.kind
            in (
                OutputKind.BUFFER_MUTATION,
                OutputKind.USER_INPUT_MUTATION,
                OutputKind.PARAMETER_MUTATION,
            )
            else None
        )
        for out_spec in ep.graph_signature.output_specs
    ]

    for node in new_gm.graph.nodes:
        source_node = None
        if node.op == "placeholder":
            source_node = placeholder_source_node_dict.get(node.target)
        else:
            if node.name in source_node_dict:
                source_node = source_node_dict.get(node.name)
        node.meta["from_node"] = [
            NodeSource(
                source_node,
                "ExportedProgram.module()",
                NodeSourceAction.CREATE,
            )
        ]

    if ep.call_spec.in_spec is None:
        raise AssertionError("ep.call_spec.in_spec cannot be None")
    new_gm = _unlift(
        new_gm,
        lifted_inputs,
        mutated_outputs,
        ep.call_spec.in_spec,
        ep.call_spec.out_spec,
        forward_arg_names=forward_arg_names,
    )
    unlift_gm = _create_stateful_graph_module(new_gm, ep.range_constraints, ep)
    unlift_gm.meta.update(ep.graph_module.meta)

    # create a _guards_fn submodule and insert a call to it after placeholders
    graph = unlift_gm.graph
    placeholders = graph.find_nodes(op="placeholder")
    if check_guards and placeholders and ep.example_inputs:
        sig = inspect.signature(unlift_gm.forward)
        input_paths = _get_input_paths(
            ep.example_inputs,
            sig,
        )

        # TODO (tmanlaibaatar)
        # This is band-aid solution to export new tracer replacing
        # shape env sources to flat_args. The real fix should be replacing
        # shape env sources to original user sources but this is quite
        # involved because you need to carefully construct new sources using
        # dynamo and replace all instances of it inside shape env. But it is
        # lot easier to manipulate after we turn them into strings and only
        # time we use these guards is during retracing or running exported program,
        # so it is probably ok to have "not useful" guards on ep for now.
        ep_guards = []
        for guard in ep._guards_code:
            ep_guards.append(_replace_sources(guard, input_paths))

        guards_code = _get_input_guards_for_graph(
            placeholders, ep.range_constraints, input_paths
        )

        ep_guards_code = _force_ep_signature_match(ep._guards_code, input_paths)
        ep_guards_code = _force_gm_signature_match(ep_guards_code, sig)
        guards_code.extend(ep_guards_code)
        unlift_gm._guards_fn = _convert_guards_code_to_fn(guards_code, input_paths)

        root_nn_module_stack = torch.fx._utils.first_call_function_nn_module_stack(
            graph
        )
        with graph.inserting_after(placeholders[-1]):
            node = graph.call_module("_guards_fn", tuple(placeholders))
            node.meta["nn_module_stack"] = root_nn_module_stack

        unlift_gm.recompile()

    return unlift_gm