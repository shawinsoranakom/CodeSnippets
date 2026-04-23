def _copy_graph_module_and_signature(
    ep: torch.export.ExportedProgram,
) -> tuple[torch.fx.GraphModule, torch.export.graph_signature.ExportGraphSignature]:
    # copy.deepcopy lets the objects override __deepcopy__ methods with graph_copy() and node_copy(),
    # and this can break placeholder names in some particular cases.
    # For example, node copying will avoid Python keywords like 'input', suffixing and renaming to 'input_1'.
    # So we manually overwrite placeholder names by reading the old graph.
    gm = copy.deepcopy(ep.graph_module)
    new_graph_signature = copy.deepcopy(ep.graph_signature)

    # iterate over old/new graph modules
    for old_gm, new_gm in zip(ep.graph_module.modules(), gm.modules()):  # type: ignore[union-attr]
        old_phs = [node for node in old_gm.graph.nodes if node.op == "placeholder"]
        new_phs = [node for node in new_gm.graph.nodes if node.op == "placeholder"]
        # iterate over placeholders
        if len(old_phs) != len(new_phs):
            raise AssertionError(
                f"Number of old placeholders ({len(old_phs)}) does not match "
                f"new placeholders ({len(new_phs)})"
            )
        for old_node, new_node in zip(old_phs, new_phs):
            new_node.name = old_node.name

    return gm, new_graph_signature