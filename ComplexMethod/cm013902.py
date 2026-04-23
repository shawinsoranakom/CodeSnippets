def dce_hop_extra_outputs(gm: torch.fx.GraphModule) -> bool:
    """
    Remove unused extra outputs from HOP calls in all submodules.

    For each subgraph output, check if any caller has a getitem for that index
    with users. If no caller uses it, remove the output.
    If the user in caller is an output node, to simply the algorithm, we do not recursively check
    if the caller's output is used further up in the call chain.

    Args:
        gm: The GraphModule to optimize

    Returns:
        True if any modifications were made, False otherwise
    """
    # Collect all subgraph usages: subgraph_id -> list of (parent_gm, subgraph_name, hop_node)
    subgraph_id_to_callers: dict[
        int, list[tuple[torch.fx.GraphModule, str, torch.fx.Node]]
    ] = collections.defaultdict(list)
    _collect_all_subgraph_usages(gm, subgraph_id_to_callers)

    if not subgraph_id_to_callers:
        return False

    modified = False

    for callers in subgraph_id_to_callers.values():
        parent_gm, subgraph_name, _ = callers[0]
        subgraph = getattr(parent_gm, subgraph_name)

        if not isinstance(subgraph, torch.fx.GraphModule):
            continue

        output_node = next(n for n in subgraph.graph.nodes if n.op == "output")
        output_args = output_node.args[0]
        if not isinstance(output_args, (tuple, list)):
            continue

        num_outputs = len(output_args)
        used_indices: set[int] = set()

        # Check which outputs are used by any caller
        for idx in range(num_outputs):
            if _is_output_used(idx, callers):
                used_indices.add(idx)

        # DCE if some outputs are unused
        if 0 < len(used_indices) < num_outputs:
            if _dce_subgraph(subgraph, callers, used_indices):
                modified = True

    return modified