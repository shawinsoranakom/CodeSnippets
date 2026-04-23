def _find_repeat_interleave_constraints(
    gm: torch.fx.GraphModule,
) -> list[tuple[str, str]]:
    """
    Find repeat_interleave operations with output_size constraints.

    Returns list of (repeats_placeholder_name, output_size_placeholder_name) pairs.
    These represent constraints where sum(repeats) must equal output_size.
    """
    constraints = []
    for node in gm.graph.nodes:
        if (
            node.op != "call_function"
            or "repeat_interleave" not in str(node.target)
            or not node.args
        ):
            continue

        output_size_node = node.kwargs.get("output_size")
        repeats_node = node.args[0]

        # Both must be FX nodes (not constants) and direct placeholders
        if (
            isinstance(repeats_node, torch.fx.Node)
            and isinstance(output_size_node, torch.fx.Node)
            and repeats_node.op == "placeholder"
            and output_size_node.op == "placeholder"
        ):
            constraints.append((str(repeats_node.target), str(output_size_node.target)))

    return constraints