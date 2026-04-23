def split_stack_to_cats(match: Match, split_sections: list[int], dim: int):
    if not isinstance(split_sections, (list, tuple)):  # Unnormalized split
        return
    split_node = next(node for node in match.nodes if node.target is torch.split)
    split_dim = get_arg_value(split_node, 2, "dim") or 0
    graph = match.graph
    threshold_to_cat = torch._inductor.config.pre_grad_fusion_options[
        "split_stack_to_cats_pass"
    ].get("threshold_to_cat", 10)
    # get the stack_node and check its inputs and meta data
    next_users = find_next_users(split_node)
    for stack_node in next_users:
        if stack_node.target != torch.stack or not is_node_meta_valid(stack_node):
            continue
        inputs = get_arg_value(stack_node, 0, "tensors")  # type: ignore[union-attr]
        new_cat_args, new_cat_args_meta = construct_cat_args(
            graph,
            stack_node,
            inputs,
            split_node,
            threshold_to_cat,
            update_args_from_split_getitem,
        )
        # At least one node would be in the returned new_cat_args
        # case 1: only one node in the new cat args, don't need to cat
        if len(new_cat_args) == 1:
            reshape_cat_node_to_stack(graph, new_cat_args[0], stack_node, split_dim)
            counters[backend]["split_stack_to_cats_pass"] += 1
            continue
        if len(new_cat_args) > 1 and len(new_cat_args) < len(inputs):
            with graph.inserting_after(stack_node):
                cat_node = graph.call_function(
                    torch.cat,
                    args=(new_cat_args,),
                    kwargs={"dim": split_dim},
                )
                cat_node.meta["example_value"] = torch.cat(  # type: ignore[arg-type]
                    new_cat_args_meta, dim=split_dim
                )
                reshape_cat_node_to_stack(graph, cat_node, stack_node, split_dim)
                counters[backend]["split_stack_to_cats_pass"] += 1