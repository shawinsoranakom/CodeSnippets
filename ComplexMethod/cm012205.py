def merge_split_squeeze(
    match: Match, split_input: torch.fx.Node, split_sizes: list[int], dim: int
):
    graph = match.graph
    split = next(node for node in match.nodes if node.target is torch.split)
    if not all(s == 1 for s in split_sizes):
        return
    if isinstance(dim, Sequence):
        return
    next_users = find_next_users(split)
    if not all(node.target is torch.squeeze for node in next_users):
        return
    with graph.inserting_before(match.output_node()):
        unbind = graph.call_function(
            torch.unbind, args=(split_input,), kwargs={"dim": dim}
        )
        if is_node_meta_valid(split_input):
            unbind.meta["example_value"] = torch.unbind(
                split_input.meta["example_value"], dim=dim
            )
        for item_index, getitem_node in sorted(
            [(getitem_node.args[1], getitem_node) for getitem_node in split.users]
        ):
            squeeze = next(iter(getitem_node.users.keys()))
            new_get_item = graph.call_function(
                operator.getitem, args=(unbind, item_index)
            )
            squeeze.replace_all_uses_with(new_get_item)
            new_get_item.meta.update(squeeze.meta)
            graph.erase_node(squeeze)
            graph.erase_node(getitem_node)
    graph.erase_node(split)
    counters[backend]["split_cat_pass"] += 1