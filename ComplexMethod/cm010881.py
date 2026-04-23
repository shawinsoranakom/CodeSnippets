def normalize_placeholder_names(
    gm: torch.fx.GraphModule,
) -> Generator[None, None, None]:
    """
    Context manager that normalizes the placeholder names in the graph module.
    This is used while generating a cache key for AOTAutogradCache, so that two graphs
    that are isomorphic when normalizing names can hit the same cache entry.
    This is safe because nothing underneath AOTAutograd uses the node names on the
    original dynamo graph: AOTAutograd re-traces with its own nodes, and guards are
    in terms of original sources rather than placeholder names.
    """
    # Standalone inductor: we're bypassing AOTAutogradCache anyway, so return the graph
    # as-is
    if not config.autograd_cache_normalize_inputs or not hasattr(gm, "graph"):
        yield
        return

    # Track all the old state of placeholders
    old_placeholder_names = []
    old_used_names = copy(gm.graph._graph_namespace._used_names)
    i = 0
    for n in gm.graph.find_nodes(op="placeholder", sort=True):
        if n.type != torch.SymInt:
            # _rename renames the node in the body of the function,
            # but it doesn't change the raw name from node.target
            # So we also set the raw_name of node.target to a new placeholder name
            new_placeholder_name = f"p_{i}"
            old_placeholder_names.append((n.name, n.target))
            n.target = new_placeholder_name
            n._rename(new_placeholder_name)
            i += 1
    gm.recompile()
    try:
        yield
    finally:
        # Used_names contains all our old placeholder names,
        # so we clear it temporarily when we put them back
        gm.graph._graph_namespace._used_names = set()
        # Restore the placeholder names
        i = 0
        for n in gm.graph.find_nodes(op="placeholder", sort=True):
            if n.type != torch.SymInt:
                (name, target) = old_placeholder_names[i]
                n.target = target
                n._rename(name)
                i += 1
        if i != len(old_placeholder_names):
            raise AssertionError(
                f"i={i} != len(old_placeholder_names)={len(old_placeholder_names)}"
            )
        # Now restore the old namespace's used names
        gm.graph._graph_namespace._used_names = old_used_names
        gm.recompile()