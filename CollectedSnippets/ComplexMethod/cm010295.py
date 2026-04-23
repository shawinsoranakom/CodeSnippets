def _verify_placeholder_names(
    gm: torch.fx.GraphModule, sig: ExportGraphSignature
) -> None:
    """
    Performs a sanity check on the placeholder node names.
    - User input nodes: no restrictions, should match the original forward() signature
    - Params/buffers/constants/custom_obj/token nodes: should start with prefixes defined in <placeholder_prefixes>
    """
    name_to_kind = {spec.arg.name: spec.kind for spec in sig.input_specs}
    for mod in gm.modules():
        if not isinstance(mod, torch.fx.GraphModule):
            continue
        for node in mod.graph.nodes:
            if node.op == "placeholder":
                if node.name not in name_to_kind:
                    continue
                node_kind = name_to_kind[node.name]
                prefix = placeholder_prefixes[node_kind]
                if not node.name.startswith(prefix):
                    raise SpecViolationError(
                        f"Placeholder node name {node.name} does not follow spec for {node_kind}, name should have prefix: {prefix}"
                    )