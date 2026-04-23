def update_args_from_split_getitem(
    graph: torch.fx.Graph,
    node: torch.fx.Node,
    getitem_indices: list[int],
    parents_seen: list[torch.fx.Node],
    new_cat_args: list[torch.fx.Node],
    new_cat_args_meta: list[torch.fx.Node],
    idx_to_getitems: dict[int, torch.fx.Node],
    threshold_to_cat: int = 2,
):
    split_input, split_size, split_dim = _get_split_args_default(parents_seen[-1])
    # case 1: the number of getitems is the same as the split size, eliminate the split
    if len(split_size) == len(getitem_indices) and is_sorted_and_consecutive(
        getitem_indices
    ):
        # we can merge the getitems from the previous parent
        new_cat_args.append(split_input)
        new_cat_args_meta.append(split_input.meta["example_value"])
    else:
        if len(getitem_indices) > 0:
            # case 2: the number of getitems is smaller than the split size but larger than the threshold, and
            # the indices of getitems are not all consecutive, we need to divide the indices into multiple groups
            geitem_indices_sublist = divide_into_consecutive_sublists(getitem_indices)
            for sublist in geitem_indices_sublist:
                if len(sublist) >= threshold_to_cat:
                    # case 2: the number of getitems is smaller than the split size but larger than the threshold
                    # we need to slice the input of parent
                    start_fused_size = sum(split_size[: sublist[0]])
                    end_fused_size = sum(split_size[: sublist[-1] + 1])
                    slice_list = []
                    for i in range(len(split_input.meta["example_value"].shape)):  # type: ignore[union-attr]
                        if i != split_dim:
                            slice_list.append(slice(None, None, None))
                        else:
                            slice_list.append(
                                slice(start_fused_size, end_fused_size, None)
                            )
                    with graph.inserting_after(node):
                        slice_node = graph.call_function(
                            operator.getitem,
                            args=(split_input, tuple(slice_list)),
                        )
                        slice_node.meta["example_value"] = split_input.meta[
                            "example_value"
                        ][tuple(slice_list)]
                        new_cat_args.append(slice_node)
                        new_cat_args_meta.append(slice_node.meta["example_value"])
                else:
                    # case 3: the number of getitems is smaller than the threshold, no merge is done
                    # get the getitems based on the indexes
                    for i in sublist:
                        new_cat_args.append(idx_to_getitems[i])
                        new_cat_args_meta.append(
                            idx_to_getitems[i].meta["example_value"]
                        )