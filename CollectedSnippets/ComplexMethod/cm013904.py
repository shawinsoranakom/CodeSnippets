def _dce_subgraph(
    subgraph: torch.fx.GraphModule,
    callers: list[tuple[torch.fx.GraphModule, str, torch.fx.Node]],
    used_indices: set[int],
) -> bool:
    """
    DCE a subgraph by removing unused output indices.

    Updates the subgraph's output node, all getitem nodes in callers,
    and example_value metadata on HOP nodes.
    """
    output_node = next(n for n in subgraph.graph.nodes if n.op == "output")
    old_outputs = list(output_node.args[0])

    # Check if this is the forward subgraph of autograd_function_apply
    # For autograd_function_apply, the fwd subgraph must return (output, saved_values, ...)
    # where indices 0 and 1 are ALWAYS required by the runtime
    # is_autograd_fwd = any(
    #     node.target == torch.ops.higher_order.autograd_function_apply
    #     for node in hop_nodes
    # )
    is_autograd_fwd = False

    # For autograd_function_apply forward subgraph, indices 0 (output) and 1 (saved_values)
    # are ALWAYS used by the runtime, even if not explicitly accessed via getitem
    if is_autograd_fwd and len(old_outputs) >= 2:
        used_indices.add(0)  # output
        used_indices.add(1)  # saved_values

    # Nothing to DCE if all outputs are used or no outputs are used
    if len(used_indices) >= len(old_outputs) or len(used_indices) == 0:
        return False

    # Build mapping from old indices to new indices
    old_to_new: dict[int, int] = {}
    new_outputs = []
    new_idx = 0

    for old_idx in range(len(old_outputs)):
        if old_idx in used_indices:
            old_to_new[old_idx] = new_idx
            new_outputs.append(old_outputs[old_idx])
            new_idx += 1

    # Update subgraph output node
    # Create a new output node with the filtered outputs
    with subgraph.graph.inserting_before(output_node):
        new_output_node = subgraph.graph.output(tuple(new_outputs))
    output_node.replace_all_uses_with(new_output_node)
    subgraph.graph.erase_node(output_node)

    for parent_gm, _, hop_node in callers:
        # Update getitem nodes to use new indices
        for user in list(hop_node.users):
            if user.op == "call_function" and user.target == operator.getitem:
                old_idx = user.args[1]
                assert isinstance(old_idx, int)

                if old_idx not in old_to_new:
                    assert len(list(user.users)) == 0
                    parent_gm.graph.erase_node(user)
                    continue

                new_idx = old_to_new[old_idx]
                # Create a new getitem node with the new index
                with parent_gm.graph.inserting_before(user):
                    new_getitem = parent_gm.graph.call_function(
                        operator.getitem, args=(user.args[0], new_idx)
                    )
                    # Copy metadata from old node
                    new_getitem.meta = user.meta.copy()
                user.replace_all_uses_with(new_getitem)
                parent_gm.graph.erase_node(user)

        # Update example_value metadata on hop_node
        if "example_value" in hop_node.meta:
            old_example = hop_node.meta["example_value"]
            assert isinstance(old_example, (tuple, list))
            new_example = tuple(
                old_example[old_idx]
                for old_idx in range(len(old_outputs))
                if old_idx in used_indices
            )
            hop_node.meta["example_value"] = new_example

    # Recompile subgraph and all modified parent graphs
    subgraph.graph.lint()
    subgraph.recompile()

    for parent_gm in {caller[0] for caller in callers}:
        parent_gm.graph.lint()
        parent_gm.recompile()

    return True