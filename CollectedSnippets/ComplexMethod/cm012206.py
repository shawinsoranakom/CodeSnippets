def merge_getitem_cat(match: Match, split_sections: list[int], dim: int):
    if not isinstance(split_sections, (list, tuple)):  # Unnormalized split
        return
    graph = match.graph
    split_node = next(node for node in match.nodes if node.target is torch.split)
    split_input, _split_size, split_dim = _get_split_args_default(split_node)
    # if the cat and split have different dims, return
    # Find the next users (i.e. users after the getitem)
    next_users = find_next_users(split_node)
    # 'immutable_list' object does not support mutation. Create a new copy of it
    split_sections = list(split_sections)
    for cat_user in next_users:
        if cat_user.target is torch.cat:
            cat_dim = get_arg_value(cat_user, 1, "dim")
            # check the all getitems in the cat_user from the same node
            # check the input of the cat has all getitem from the split
            # check all getitem only has one single user
            if (
                split_dim != cat_dim
                or not has_same_parent_node(cat_user)
                or not all(len(arg.users) == 1 for arg in cat_user.args[0])  # type: ignore[union-attr]
            ):
                continue
            # find the index of getitems to be cated/stacked
            # type: ignore[union-attr]
            indices = [arg.args[1] for arg in cat_user.args[0]]  # type: ignore[union-attr]
            # the getitems to be merged must be consecutive, otherwise
            # returned sliced tensor could be wrong
            if not is_sorted_and_consecutive(indices):  # type: ignore[arg-type]
                continue
            # update the arg of cat user, only keep the first getitem
            cat_user.update_arg(0, cat_user.args[0][0])  # type: ignore[index]
            # calculate the fused tensor sizes in the indices
            fused_tensor_size = 0
            for i in range(len(split_node.args[1])):  # type: ignore[arg-type]
                if i in indices:
                    fused_tensor_size += split_node.args[1][i]  # type: ignore[operator, assignment, index]
            # update the split sections
            split_sections[indices[0]] = calculate_fused_tensor_size(  # type: ignore[index]
                split_node,
                indices,  # type: ignore[arg-type]
            )
            # padding others with zeros to keep the same dict size
            for i in indices[1:]:
                split_sections[i] = 0  # type: ignore[index]
            # remove all unused indexes in the split_node
            new_split_sections, index_mapping = remove_zeros(split_sections)
            with graph.inserting_after(split_node):
                new_split_node = graph.call_function(
                    torch.split,
                    args=(split_input, split_sections),
                    kwargs={"dim": split_dim},
                )
                split_node.replace_all_uses_with(new_split_node)
                new_split_node.meta.update(split_node.meta)
                # remove all unused getitem nodes
                to_remove = [cat_user]
                # dictionary keys changed during iteration
                new_split_getitem_nodes = list(new_split_node.users.keys())
                for getitem_node in new_split_getitem_nodes:
                    if getitem_node.args[1] in indices[1:]:
                        to_remove.append(getitem_node)
                    # update meta data of getitem
                    elif getitem_node.args[1] == indices[0]:
                        cat_user.replace_all_uses_with(getitem_node)
                        getitem_node.meta.update(cat_user.meta)
                    else:
                        # update getitem index for new split node
                        getitem_node.update_arg(1, index_mapping[getitem_node.args[1]])
                graph.erase_node(split_node)
                for getitem_node in to_remove:
                    graph.erase_node(getitem_node)
                # update the split sections of new split node
                new_split_node.update_arg(1, new_split_sections)
                split_node = new_split_node
                split_sections = new_split_sections

                counters[backend]["merge_getitem_cat_pass"] += 1