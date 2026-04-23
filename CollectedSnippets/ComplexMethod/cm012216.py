def construct_cat_args(
    graph: torch.fx.Graph,
    cat_or_stack_node: torch.fx.Node,
    inputs: list[torch.fx.Node],
    split_or_unbind_node: torch.fx.Node,
    threshold_to_cat: int = 2,
    run_update_func: Callable = update_args_from_split_getitem,  # type: ignore[type-arg]
) -> tuple[list[torch.fx.Node], list[torch.Tensor]]:
    new_cat_args, parents_seen, getitem_indices, idx_to_getitems = [], [], [], {}  # type: ignore[var-annotated]
    new_cat_args_meta = []  # type: ignore[var-annotated]
    for input in inputs:
        if input.target != operator.getitem:
            # update the last arg based on getitem_indices and parents_seens
            if len(parents_seen) > 0:
                run_update_func(  # type: ignore[arg-type, union-attr]
                    graph,
                    cat_or_stack_node,
                    getitem_indices,
                    parents_seen,
                    new_cat_args,
                    new_cat_args_meta,
                    idx_to_getitems,  # type: ignore[arg-type, union-attr]
                    threshold_to_cat,
                )
            new_cat_args.append(input)
            new_cat_args_meta.append(input.meta["example_value"])
            # reset the indices array
            getitem_indices, idx_to_getitems = [], {}
        else:
            # get the parent node of the getitem input
            parent, idx = input.args[0], input.args[1]  # type: ignore[union-attr]
            if parent.target != split_or_unbind_node.target:  # type: ignore[union-attr]
                new_cat_args.append(input)
                new_cat_args_meta.append(input.meta["example_value"])
                continue
            # cannot use parents_seen to check since the first item could be non getitem node
            if len(parents_seen) == 0:
                parents_seen.append(parent)
                idx_to_getitems[idx] = input
                getitem_indices.append(idx)
                # case: we only have one getitem input, and it is in the last position
                if input == inputs[-1]:
                    new_cat_args.append(input)
                    new_cat_args_meta.append(input.meta["example_value"])
                continue
                # if it is the last input in the tensors, we also check if it can be optimized
            if parent != parents_seen[-1] or input == inputs[-1]:
                if input == inputs[-1]:
                    getitem_indices.append(idx)
                    idx_to_getitems[idx] = input
                run_update_func(  # type: ignore[arg-type, union-attr]
                    graph,
                    cat_or_stack_node,
                    getitem_indices,
                    parents_seen,
                    new_cat_args,
                    new_cat_args_meta,
                    idx_to_getitems,  # type: ignore[arg-type, union-attr]
                    threshold_to_cat,
                )
                # reset the indices array for the next parent
                # remember to add the last element since it is the first
                # item in this round of parent
                # add the parent to the list of seen parents
                parents_seen.append(parent)
                getitem_indices, idx_to_getitems = [idx], {idx: input}
            else:
                getitem_indices.append(idx)
                idx_to_getitems[idx] = input
    return new_cat_args, new_cat_args_meta