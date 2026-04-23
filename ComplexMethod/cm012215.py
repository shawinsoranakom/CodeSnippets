def update_args_from_unbind_getitem(
    graph: torch.fx.Graph,
    node: torch.fx.Node,  # cat or stack node
    getitem_indices: list[int],
    parents_seen: list[torch.fx.Node],
    new_cat_args: list[torch.fx.Node],
    new_cat_args_meta: list[torch.fx.Node],
    idx_to_getitems: dict[int, torch.fx.Node],
    threshold_to_cat: int = 2,
):
    unbind_input = get_arg_value(parents_seen[-1], 0, "input")  # split or unbind input
    unbind_dim = get_arg_value(parents_seen[-1], 1, "dim")  # split or unbind dim
    cat_dim = get_arg_value(node, 1, "dim")  # cat or stack dim
    # case 1: the number of getitems is the same as the split size, eliminate the split
    size = list(unbind_input.meta["example_value"].shape)[unbind_dim]
    if size == len(getitem_indices):
        cat_shape = torch.cat(
            [idx_to_getitems[i].meta["example_value"] for i in getitem_indices],
            dim=cat_dim,
        ).shape
        # we can merge the getitems from the previous parent
        reshape_node = reshape_cat_node(
            graph, node, unbind_input, cat_dim, unbind_dim, cat_shape
        )
        new_cat_args.append(reshape_node)
        new_cat_args_meta.append(reshape_node.meta["example_value"])
    elif len(getitem_indices) >= threshold_to_cat and is_sorted_and_consecutive(
        getitem_indices
    ):
        # case 2: the number of getitems is smaller than the split size but larger than the threshold
        # we need to slice the input of parent
        cat_shape = torch.cat(
            [idx_to_getitems[i].meta["example_value"] for i in getitem_indices],
            dim=cat_dim,
        ).shape
        slice_list = []
        for i in range(len(cat_shape) + 1):
            if i != unbind_dim:
                slice_list.append(slice(None, None, None))  # start, end, step
            else:
                slice_list.append(
                    slice(getitem_indices[0], getitem_indices[-1] + 1, None)
                )
        with graph.inserting_after(node):
            slice_node = graph.call_function(
                operator.getitem,
                args=(unbind_input, tuple(slice_list)),
            )
            slice_node.meta["example_value"] = torch.narrow(
                unbind_input.meta["example_value"],
                unbind_dim,
                getitem_indices[0],
                getitem_indices[-1] - getitem_indices[0] + 1,
            )
            reshape_node = reshape_cat_node(
                graph, node, slice_node, cat_dim, unbind_dim, cat_shape
            )
            new_cat_args.append(reshape_node)
            new_cat_args_meta.append(reshape_node.meta["example_value"])
    else:
        # case 3: the number of getitems is smaller than the threshold, no merge is done
        # get the getitems based on the indexes
        for i in getitem_indices:
            new_cat_args.append(idx_to_getitems[i])
            new_cat_args_meta.append(idx_to_getitems[i].meta["example_value"])