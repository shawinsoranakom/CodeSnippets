def normalize_cat_default(match: Match, *args, **kwargs):
    cat_node = match.nodes[0]
    graph = match.graph
    tensors = get_arg_value(cat_node, 0, "tensors")
    cat_dim = get_arg_value(cat_node, 1, "dim")
    if cat_dim is None:
        cat_axis = cat_node.kwargs.get("axis")
        if cat_axis is not None:
            cat_dim = cat_axis
        else:
            cat_dim = 0
    if tensors is None or cat_dim is None:
        log.debug("couldn't find cat args")
        return
    assert isinstance(tensors, (list, tuple))
    for tensor in itertools.chain([cat_node], tensors):
        if not is_node_meta_valid(tensor):
            log.debug("example value absent for node: %s", tensor)
            return

    ndim = cat_node.meta["example_value"].dim()

    def is_empty_tensor(x):
        # special case where torch.cat supports cat'ing with an empty tensor
        x_shape = x.meta["example_value"].shape
        return len(x_shape) == 1 and guard_or_false(x_shape[0] == 0)

    assert all(
        ndim == x.meta["example_value"].dim() or is_empty_tensor(x) for x in tensors
    )

    if cat_dim < 0:  # Normalize cat dim
        cat_dim += ndim

    new_args = (tensors,)
    new_kwargs = {"dim": cat_dim}
    if (
        cat_node.args == new_args
        and cat_node.kwargs == new_kwargs
        and cat_node.op == "call_function"
        and cat_node.target is torch.cat
    ):
        return

    with graph.inserting_after(cat_node):
        new_cat_node = graph.call_function(
            torch.cat,
            args=new_args,
            kwargs=new_kwargs,
        )
    cat_node.replace_all_uses_with(new_cat_node)
    new_cat_node.meta.update(cat_node.meta)
    graph.erase_node(cat_node)
    counters[backend]["normalization_pass"] += 1