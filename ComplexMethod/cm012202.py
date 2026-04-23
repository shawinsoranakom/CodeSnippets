def normalize_stack_default(match: Match, *args, **kwargs):
    node = match.nodes[0]
    graph = match.graph
    tensors = get_arg_value(node, 0, "tensors")
    dim = get_arg_value(node, 1, "dim") or 0
    if tensors is None or dim is None:
        log.debug("couldn't find stack args")
        return
    assert isinstance(tensors, (list, tuple))

    # A bug in pytorch, some nodes miss the example_value metadata
    for tensor in itertools.chain([node], tensors):
        if not is_node_meta_valid(tensor):
            log.debug("example value absent for node: %s", tensor)
            return

    ndim = node.meta["example_value"].dim()
    if dim < 0:  # Normalize dim
        dim += ndim

    with graph.inserting_after(node):
        new_node = graph.call_function(
            node.target,  # type: ignore[arg-type]
            args=(tensors,),
            kwargs={"dim": dim},
        )
    node.replace_all_uses_with(new_node)
    new_node.meta.update(node.meta)
    graph.erase_node(node)
    counters[backend]["normalization_pass"] += 1