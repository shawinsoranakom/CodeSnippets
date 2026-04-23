def unbind_cat_to_view(match: Match, unbind_input: torch.fx.Node, dim: int):
    unbind_node = next(node for node in match.nodes if node.target is torch.unbind)
    graph = match.graph
    # get the cat_node and check its inputs and meta data
    next_users = find_next_users(unbind_node)
    threshold_to_cat = torch._inductor.config.pre_grad_fusion_options[
        "unbind_cat_to_view_pass"
    ].get("threshold_to_cat", 10)
    # get the cat_node and check its inputs and meta data
    for cat_node in next_users:
        if cat_node.target != torch.cat or not is_node_meta_valid(cat_node):
            continue
        inputs = get_arg_value(cat_node, 0, "tensors")  # type: ignore[union-attr]
        new_cat_args, new_cat_args_meta = construct_cat_args(
            graph,
            cat_node,
            inputs,
            unbind_node,
            threshold_to_cat,
            update_args_from_unbind_getitem,
        )
        # get the view shape
        # At least one node would be in the returned new_cat_args
        # case 1: only one node in the new cat args, don't need to cat
        if len(new_cat_args) == 1:
            cat_node.replace_all_uses_with(new_cat_args[0])
            # remove inputs of cat_node if they have no users
            cat_inputs = cat_node.args[0]  # type: ignore[union-attr]
            graph.erase_node(cat_node)
            remove_split_unbind_children(graph, cat_inputs)  # type: ignore[arg-type]
            counters[backend]["unbind_cat_to_view_pass"] += 1
            continue
        if len(new_cat_args) > 1 and len(new_cat_args) < len(inputs):
            # get the view shape
            cat_dim = get_arg_value(cat_node, 1, "dim")
            with graph.inserting_after(cat_node):
                new_cat_node = graph.call_function(
                    torch.cat,
                    args=(new_cat_args,),
                    kwargs={"dim": cat_dim},
                )
                new_cat_node.meta["example_value"] = torch.cat(
                    new_cat_args_meta, dim=cat_dim
                )  # type: ignore[arg-type]
                cat_node.replace_all_uses_with(new_cat_node)
                new_cat_node.meta.update(cat_node.meta)
            # remove inputs of cat_node if they have no users
            cat_inputs = cat_node.args[0]  # type: ignore[union-attr]
            graph.erase_node(cat_node)
            remove_split_unbind_children(graph, cat_inputs)  # type: ignore[arg-type]
            counters[backend]["unbind_cat_to_view_pass"] += 1