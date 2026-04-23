def merge_splits(
    match: Match,
    first_split_input: torch.fx.Node,
    first_split_sections: list[int],
    next_split_sections: list[int],
    # Note: dim is implicitly passed by TorchSplit, as it internally uses a pattern with dim
    dim: int,
):
    node = match.output_node()
    # it is possible that the split has no users,
    # we check the corner case and skip the pattern
    if len(node.users.keys()) == 0:
        return
    graph = match.graph
    first_split = node.args[0].args[0]  # type: ignore[union-attr]
    next_split_index = node.args[0].args[1]  # type: ignore[union-attr]

    new_split_sections = list(first_split_sections)
    new_split_sections[next_split_index : next_split_index + 1] = next_split_sections  # type: ignore[operator, misc]

    first_split_dim = _get_dim(first_split)

    to_remove = []

    with graph.inserting_before(first_split):  # type: ignore[arg-type]
        # Add the new split node
        new_split = graph.call_function(
            torch.split,
            args=(first_split_input, new_split_sections),
            kwargs={"dim": first_split_dim},
        )
        if is_node_meta_valid(first_split_input):
            new_split.meta["example_value"] = torch.split(
                first_split_input.meta["example_value"],
                new_split_sections,
                dim=first_split_dim,
            )
        first_split_num_to_user = {
            user.args[1]: user
            for user in first_split.users  # type: ignore[union-attr]
        }

        new_split_num = 0
        for split_num in range(len(first_split_sections)):
            if split_num not in first_split_num_to_user:
                new_split_num += 1
                continue
            old_getitem = first_split_num_to_user[split_num]
            if split_num != next_split_index:
                old_getitem.update_arg(0, new_split)
                old_getitem.update_arg(1, new_split_num)
                new_split_num += 1
            else:
                next_split_num_to_user = {user.args[1]: user for user in node.users}
                # It is not necessary all getitems from the split node are used.
                for next_split_num in range(len(next_split_sections)):
                    with graph.inserting_after(new_split):
                        new_getitem = graph.call_function(
                            operator.getitem, args=(new_split, new_split_num)
                        )
                    new_split_num += 1
                    if next_split_num not in next_split_num_to_user:
                        continue
                    next_getitem = next_split_num_to_user[next_split_num]
                    new_getitem.meta.update(next_getitem.meta)
                    next_getitem.replace_all_uses_with(new_getitem)
                    to_remove.append(next_getitem)
                to_remove.append(node)
                to_remove.append(old_getitem)

        to_remove.append(first_split)  # type: ignore[arg-type]
    for node in to_remove:
        graph.erase_node(node)

    counters[backend]["merge_splits_pass"] += 1