def mutate_cat_node(match: Match, split_sections: list[int], dim: int):
    if not isinstance(split_sections, (list, tuple)):  # Unnormalized split
        return
    graph = match.graph
    split_node = next(node for node in match.nodes if node.target is torch.split)
    _split_input, _split_size, split_dim = _get_split_args_default(split_node)
    # if the cat and split have different dims, return
    # Find the next users (i.e. users after the getitem)
    next_users = find_next_users(split_node)
    for cat_user in next_users:
        if cat_user.target is torch.cat:
            cat_dim = get_arg_value(cat_user, 1, "dim") or 0
            # check that all getitems in the cat_user from the same node
            # check the input of the cat has all getitem from the split
            if split_dim != cat_dim or not has_same_parent_node(cat_user):
                continue
            # find the index of getitems to be cat
            indices, idx_to_getitem = [], {}
            for getitem in cat_user.args[0]:  # type: ignore[union-attr]
                indices.append(getitem.args[1])  # type: ignore[union-attr]
                idx_to_getitem[getitem.args[1]] = getitem  # type: ignore[union-attr]
            # the getitems to be merged must be consecutive, otherwise
            # returned sliced tensor could be wrong
            if not is_sorted_and_consecutive(indices):  # type: ignore[arg-type]
                continue
            # case 1: the cat uses all getitems from the split
            if len(split_sections) == len(cat_user.args[0]):  # type: ignore[arg-type]
                # replace the users of the cat node to be the input of the split node
                cat_user.replace_all_uses_with(split_node.args[0])  # type: ignore[arg-type]
                # remove the cat node
                graph.erase_node(cat_user)
                counters[backend]["mutate_cat_pass"] += 1
            # case 2: the cat uses some getitems from the split
            elif is_node_meta_valid(split_node.args[0]):  # type: ignore[arg-type]
                # check the split dim, and construct the slice tuple
                start_fused_size = calculate_fused_tensor_size(
                    split_node,
                    list(range(indices[0])),  # type: ignore[arg-type]
                )
                end_fused_size = start_fused_size + calculate_fused_tensor_size(
                    split_node,
                    indices,  # type: ignore[arg-type]
                )
                slice_list = []
                for i in range(len(split_node.args[0].meta["example_value"].shape)):  # type: ignore[union-attr]
                    if i != split_dim:
                        slice_list.append(slice(None, None, None))
                    else:
                        slice_list.append(slice(start_fused_size, end_fused_size, None))
                with graph.inserting_after(split_node):
                    slice_node = graph.call_function(
                        operator.getitem,
                        args=(split_node.args[0], tuple(slice_list)),
                    )
                    cat_user.replace_all_uses_with(slice_node)
                    slice_node.meta.update(cat_user.meta)

                # remove the cat node
                graph.erase_node(cat_user)
                counters[backend]["mutate_cat_pass"] += 1