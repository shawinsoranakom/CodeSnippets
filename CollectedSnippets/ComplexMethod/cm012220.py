def unbind_stack_to_slices(match: Match, unbind_input: torch.fx.Node, dim: int):
    unbind_node = next(node for node in match.nodes if node.target is torch.unbind)
    graph = match.graph
    # get the cat_node and check its inputs and meta data
    next_users = find_next_users(unbind_node)
    threshold_to_cat = torch._inductor.config.pre_grad_fusion_options[
        "unbind_stack_to_slices_pass"
    ].get("threshold_to_cat", 10)
    # get the cat_node and check its inputs and meta data
    for stack_node in next_users:
        if stack_node.target != torch.stack or not is_node_meta_valid(stack_node):
            continue
        inputs = get_arg_value(stack_node, 0, "tensors")  # type: ignore[union-attr]
        new_cat_args, new_cat_args_meta = construct_cat_args(
            graph,
            stack_node,
            inputs,
            unbind_node,
            threshold_to_cat,
            update_args_from_unbind_getitem,
        )
        unbind_dim = get_arg_value(unbind_node, 1, "dim") or 0
        # At least one node would be in the returned new_cat_args
        # case 1: only one node in the new cat args, don't need to cat
        if len(new_cat_args) == 1:
            reshape_cat_node_to_stack(graph, new_cat_args[0], stack_node, unbind_dim)
            counters[backend]["unbind_stack_to_slices_pass"] += 1
            continue
        if len(new_cat_args) > 1 and len(new_cat_args) < len(inputs):
            # get the view shape
            cat_dim = get_arg_value(stack_node, 1, "dim")
            with graph.inserting_after(stack_node):
                new_cat_node = graph.call_function(
                    torch.cat,
                    args=(new_cat_args,),
                    kwargs={"dim": cat_dim},
                )
                new_cat_node.meta["example_value"] = torch.cat(
                    new_cat_args_meta, dim=cat_dim
                )
                reshape_cat_node_to_stack(graph, new_cat_node, stack_node, unbind_dim)
            counters[backend]["unbind_stack_to_slices_pass"] += 1