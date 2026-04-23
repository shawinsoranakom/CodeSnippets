def _wrap_sync_node(
    gm: torch.fx.GraphModule,
    sync_node: Node,
    deps_before_sync: list[Node],
    visited: set[Node],
) -> tuple[Node, list[Node]]:
    """
    Core logic: wrap a single sync node in control_deps.

    Returns (control_deps_node, passthrough_getitems) where passthrough_getitems
    are the getitem nodes that thread dependencies through the control_deps node.
    ``visited`` is the set of nodes at or before the sync node in graph order,
    used to distinguish pre-sync vs post-sync users.
    """
    from torch._inductor.fx_passes.control_dependencies import (
        _create_subgraph_for_node,
        control_deps,
        get_subgraph_name,
    )

    graph = gm.graph

    # Use dep.users to find deps with uses after the sync — avoids a forward walk.
    deps_with_uses_after_sync = [
        dep
        for dep in deps_before_sync
        if any(user not in visited for user in dep.users)
    ]

    # Create subgraph that executes sync and passes through only used dependencies
    subgraph_module = _create_subgraph_for_node(
        graph, sync_node, deps_with_uses_after_sync
    )
    subgraph_attr_name = get_subgraph_name(gm, sync_node.name)
    setattr(gm, subgraph_attr_name, subgraph_module)

    # Create control_deps call
    # Note: sync nodes (record_event/wait_event) only take int args, no Node args.
    with graph.inserting_before(sync_node):
        get_subgraph = graph.get_attr(subgraph_attr_name)
        control_deps_node = graph.call_function(
            control_deps,
            args=(
                tuple(deps_before_sync),  # additional_deps (all deps for ordering)
                get_subgraph,  # subgraph
                *deps_with_uses_after_sync,  # only pass through deps that are used
            ),
            kwargs={},
        )

    # Mark newly created nodes as visited so subsequent syncs don't
    # misclassify them as "after the sync" during replacement.
    visited.add(get_subgraph)
    visited.add(control_deps_node)

    # The output is (sync_result, *deps_with_uses_after_sync)
    # Create getitem nodes only for dependencies that have uses after sync
    replacements: dict[Node, Node] = {}
    with graph.inserting_after(control_deps_node):
        for i, dep in enumerate(deps_with_uses_after_sync):
            getitem_node = graph.call_function(
                operator.getitem,
                args=(control_deps_node, i + 1),  # +1 because index 0 is sync result
            )
            getitem_node.meta.update(dep.meta)
            replacements[dep] = getitem_node
            visited.add(getitem_node)

    # Replace uses of dependencies that come after sync_node.
    # Use map_arg to handle nested structures (e.g. output node's list args).
    for dep, getitem_node in replacements.items():
        for user in list(dep.users.keys()):
            if user is control_deps_node:
                continue
            if user in visited:
                continue
            # Don't replace forward outputs in the output node — they belong
            # to the forward partition and must not reference backward nodes.
            if user.op == "output" and not is_bwd_node(dep):
                continue

            def _replace(n: Node) -> Node:
                return getitem_node if n is dep else n

            user.args = map_arg(user.args, _replace)
            user.kwargs = map_arg(user.kwargs, _replace)

    # Remove original sync node
    sync_node.replace_all_uses_with(control_deps_node)
    graph.erase_node(sync_node)
    return control_deps_node, list(replacements.values())