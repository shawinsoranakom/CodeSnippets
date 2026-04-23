def _unlift_graph(
    mod: GraphModule, gm: GraphModule, graph_signature: GraphSignature
) -> GraphModule:
    from torch.export.unflatten import _assign_attr, _AttrKind

    _resolve_name_collision(mod, gm)

    state_dict: dict[str, torch.nn.parameter.Parameter | torch.Tensor] = {}
    for name, param in mod.named_parameters(remove_duplicate=False):
        state_dict[name] = param
        _assign_attr(
            param,
            gm,
            name,
            attr_kind=_AttrKind.PARAMETER,
        )
    for name, buffer in mod.named_buffers(remove_duplicate=False):
        state_dict[name] = buffer
        _assign_attr(
            buffer,
            gm,
            name,
            attr_kind=_AttrKind.BUFFER,
        )

    placeholder_nodes = gm.graph.find_nodes(op="placeholder")
    lifted_inputs: list[FQN | None] = []

    # In AOTI, module parameters and buffers are not lifted as graph inputs.
    # As a result, mutation to buffers has side effect which makes their initial
    # values different from Eager. So we clone them here as a copy.
    # We are not cloning for parameters, although it will be needed if we want to
    # support training.
    for node in placeholder_nodes:
        node_name = node.name
        if node_name in graph_signature.inputs_to_parameters:
            parameter_name = graph_signature.inputs_to_parameters[node_name]
            lifted_inputs.append(parameter_name)
        elif node_name in graph_signature.inputs_to_buffers:
            buffer_name = graph_signature.inputs_to_buffers[node_name]
            lifted_inputs.append(buffer_name)
            gm.meta[get_cloned_parameter_buffer_name(buffer_name)] = (
                clone_preserve_strides(state_dict[buffer_name])
            )
        else:
            assert node_name in graph_signature.user_inputs
            lifted_inputs.append(None)

    from torch.export._unlift import _unlift

    outputs: tuple[torch.fx.Node, ...] = tuple(gm.graph.output_node().args[0])  # type: ignore[arg-type]
    mutated_outputs = []
    buffer_mutations = graph_signature.buffers_to_mutate
    user_input_mutations = graph_signature.user_inputs_to_mutate
    output_tokens = graph_signature.output_tokens
    for idx, out in enumerate(outputs):
        value: FQN | GraphInputName | None = None

        if idx < len(buffer_mutations) + len(user_input_mutations) + len(output_tokens):
            name = GraphOutputName(out.name)
            if name in buffer_mutations:
                value = buffer_mutations[name]
            elif name in user_input_mutations:
                value = user_input_mutations[name]

        mutated_outputs.append(value)

    unlifted_gm = _unlift(
        gm,
        lifted_inputs,
        mutated_outputs,
        pytree.treespec_leaf(),
        None,
    )
    # After unlifting, the buffer mutation information is lost. Pass the information
    # so that Inductor can do optimizations correctly.
    unlifted_gm.meta["mutated_named_buffers"] = OrderedSet(buffer_mutations.values())
    return unlifted_gm