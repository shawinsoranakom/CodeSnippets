def _rename_constants_nodes(
    gm: torch.fx.GraphModule,
    graph_signature: ExportGraphSignature,
) -> None:
    """
    For strict mode, rename constants nodes that were previously annotated as buffers.
    """
    # handle name collisions with existing constants
    node_names = {node.name for node in gm.graph.nodes}

    def rename_constant(name):
        if name in node_names:
            n = 1
            while (dup_name := f"{name}_{n}") in node_names:
                n += 1
            # pyrefly: ignore [unbound-name]
            name = dup_name
        node_names.add(name)
        return name

    # use input specs to map names from buffers to constants
    buffer_prefix = placeholder_prefixes[InputKind.BUFFER]
    const_prefix = placeholder_prefixes[InputKind.CONSTANT_TENSOR]
    buffer_to_constant = {}
    for spec in graph_signature.input_specs:
        if spec.kind == InputKind.CONSTANT_TENSOR and not spec.arg.name.startswith(
            const_prefix
        ):
            if spec.arg.name.startswith(buffer_prefix):  # map from buffer to constants
                c_name = rename_constant(
                    const_prefix + spec.arg.name[len(buffer_prefix) :]
                )
            else:  # lifted constant
                c_name = rename_constant(const_prefix + spec.arg.name)
            buffer_to_constant[spec.arg.name] = c_name
            spec.arg.name = c_name
    for spec in graph_signature.output_specs:
        if spec.arg.name in buffer_to_constant:
            spec.arg.name = buffer_to_constant[spec.arg.name]

    # Rename constants nodes for all modules
    for mod in gm.modules():
        if not isinstance(mod, torch.fx.GraphModule):
            continue
        for node in mod.graph.nodes:
            if node.name in buffer_to_constant:
                node.name = node.target = buffer_to_constant[node.name]
        mod.recompile()