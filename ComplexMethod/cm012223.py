def move_view_after_cat(match: Match, *args, **kwargs):
    split_node = next(
        node
        for node in match.nodes
        if node.target is torch.ops.aten.split_with_sizes.default
    )
    split_input, split_section, split_dim = _get_split_args_default(split_node)
    split_users = list(split_node.users.keys())
    getitem_indices = [
        getitem.args[1] for getitem in split_users if getitem.target is operator.getitem
    ]
    if not is_sorted_and_consecutive(getitem_indices):  # type: ignore[arg-type]
        return
    cat_nodes = [
        node for node in match.nodes if node.target is torch.ops.aten.cat.default
    ]
    graph = match.graph
    for cat_node in cat_nodes:
        if not is_node_meta_valid(cat_node):
            log.debug("example value absent for node: %s", cat_node)
            continue
        cat_dim = _get_dim(cat_node)
        cat_inputs = get_arg_value(cat_node, 0, "tensors")  # type: ignore[union-attr]
        # we only consider the following special case
        if len(cat_inputs) != len(split_section):
            continue
        # check if the cat inputs are all the view nodes
        if not all(
            view_node.target is torch.ops.aten.reshape.default
            for view_node in cat_inputs
        ):
            continue
        # check if the view nodes are all from getitem nodes
        if not all(
            view_node.args[0].target is operator.getitem for view_node in cat_inputs
        ):
            continue
        view_indices = [view.args[0].args[1] for view in cat_inputs]
        if not is_sorted_and_consecutive(view_indices):  # type: ignore[arg-type]
            continue
        if cat_dim != split_dim:
            # construct permute node
            permute_list = list(range(len(cat_node.meta["val"].shape) + 1))
            permute_list[split_dim], permute_list[cat_dim] = (
                permute_list[cat_dim],
                permute_list[split_dim],
            )
            permute_node = graph.call_function(
                torch.ops.aten.permute.default,
                args=(split_input, permute_list),
            )
        else:
            permute_node = split_input

        with graph.inserting_before(cat_node):
            view_node = graph.call_function(
                torch.ops.aten.reshape.default,
                args=(permute_node, list(cat_node.meta["val"].shape)),
            )
            cat_node.replace_all_uses_with(view_node)
            view_node.meta.update(cat_node.meta)
            graph.erase_node(cat_node)
        counters[backend]["move_view_after_cat_aten_pass"] += 1