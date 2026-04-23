def _get_updated_module_call_graph(
    old_gm: torch.fx.GraphModule,
    old_graph_signature: ExportGraphSignature,
    gm: torch.fx.GraphModule,
    graph_signature: ExportGraphSignature,
    old_module_call_graph: list[ModuleCallEntry],
):
    new_module_call_graph = copy.deepcopy(old_module_call_graph)

    old_nodes = {node.name: node for node in old_gm.graph.nodes}

    old_graph_params_buffers = {
        **old_graph_signature.inputs_to_parameters,
        **old_graph_signature.inputs_to_buffers,
    }
    new_graph_params_buffers = {
        **graph_signature.inputs_to_parameters,
        **graph_signature.inputs_to_buffers,
    }

    # use node-level provenance metadata to create a map
    # from old node names to new node names
    provenance: dict[str, str] = {}

    user_input_counter = 0
    old_user_input_names = [
        node.target for node in old_gm.graph.nodes if node.op == "placeholder"
    ]
    old_user_input_names = list(
        filter(
            lambda x: x not in old_graph_params_buffers
            and x not in old_graph_signature.input_tokens,
            old_user_input_names,
        )
    )
    new_user_input_names = [
        node.target for node in gm.graph.nodes if node.op == "placeholder"
    ]

    for node in gm.graph.nodes:
        if history := node.meta.get("from_node", []):
            provenance[history[-1].name] = node.name

        # For params and buffers, we might have applied parameterizaiton rule
        # so that the names might have changed. But for user inputs, we know we
        # must preserve the old name.
        elif node.op == "placeholder":
            if not (
                node.target in new_graph_params_buffers
                or node.target in graph_signature.input_tokens
            ):
                if node.target in new_user_input_names:
                    if not isinstance(node.name, str):
                        raise AssertionError(
                            f"expected node.name to be str, got {type(node.name)}"
                        )
                    old_name = old_user_input_names[user_input_counter]
                    if not isinstance(old_name, str):
                        raise AssertionError(
                            f"expected old_name to be str, got {type(old_name)}"
                        )
                    provenance[old_name] = node.name
                    user_input_counter += 1

    # For all the parameters and buffers, we first see
    # if they are result of parametrizations and if they
    # are, we log them and error later
    old_param_to_desugared = defaultdict(list)
    for name, target in new_graph_params_buffers.items():
        # if the parameters are not parametrized, the naming won't change.
        if not target.startswith("parametrizations."):
            # If we are in strict mode, we can't just reuse the param names
            if name in old_graph_params_buffers:
                provenance[name] = name
        else:
            old_target = ".".join(target.split(".")[1:-1])
            old_param_to_desugared[old_target].append(name)

    # map old names to new names in module call signatures
    for entry in new_module_call_graph:
        signature = entry.signature
        if signature is None:
            continue
        for x in [*signature.inputs, *signature.outputs]:
            # We noticed that submodule is taking subclass as input. we can't
            # preserve signature here.
            if x.name in old_param_to_desugared:
                raise ValueError(
                    f"It looks like {x.name} is a tensor subclass. "
                    f"Preserving submodule that takes subclass parameter is not supported"
                    f" in inference IR because we desugar them, resulting in more tensors"
                )

            if x.name in provenance:
                x.name = provenance[x.name]

            # This can happen when aten.to is called at graph boundaries.
            # Basically aten.to at post-dispatch level can either be copy
            # or alias. In the alias case, we will no-op it so it will
            # disappear from the graph. If we detect such case, we should
            # reuse the input to aten.to as the new input to the submodule.
            # Technically this can happen for other maybe aliasing ops,
            # but aten.to is probably the most common one.
            elif x.name in old_nodes:
                old_node = old_nodes[x.name]
                if old_node.op == "call_function" and old_node.target in [
                    torch.ops.aten.to.dtype_layout,
                    torch.ops.aten.to.device,
                    torch.ops.aten.to.dtype,
                ]:
                    old_target = old_node.args[0].name
                    if old_target not in provenance:
                        raise ValueError(
                            f"It looks like {old_target} is a tensor subclass. "
                            f"Preserving submodule that takes subclass parameter is not supported"
                            f" in inference IR because we desugar them, resulting in more tensors"
                        )

                    x.name = provenance[old_target]

    return new_module_call_graph