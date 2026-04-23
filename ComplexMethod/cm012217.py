def split_cat_to_slices(match: Match, split_sections: list[int], dim: int):
    if not isinstance(split_sections, (list, tuple)):  # Unnormalized split
        return
    split_nodes = [node for node in match.nodes if node.target is torch.split]
    if split_nodes:
        split_node = next(node for node in split_nodes)
    else:
        # Handle the case where there are no nodes with a target of torch.split
        return
    split_dim = get_arg_value(split_node, 2, "dim") or 0
    graph = match.graph
    threshold_to_cat = torch._inductor.config.pre_grad_fusion_options[
        "split_cat_to_slices_pass"
    ].get("threshold_to_cat", 10)
    # get the cat_node and check its inputs and meta data
    next_users = find_next_users(split_node)
    for cat_node in next_users:
        if cat_node.target != torch.cat or not is_node_meta_valid(cat_node):
            continue
        cat_inputs = get_arg_value(cat_node, 0, "tensors")  # type: ignore[union-attr]
        new_cat_args, _ = construct_cat_args(
            graph,
            cat_node,
            cat_inputs,
            split_node,
            threshold_to_cat,
            update_args_from_split_getitem,
        )
        # At least one node would be in the returned new_cat_args
        # case 1: if new cat args has length 1, we can remove the cat node
        if len(new_cat_args) == 1:
            cat_node.replace_all_uses_with(new_cat_args[0])
            # remove inputs of cat_node if they have no users
            cat_inputs = cat_node.args[0]  # type: ignore[union-attr]
            graph.erase_node(cat_node)
            remove_split_unbind_children(graph, cat_inputs)  # type: ignore[arg-type]
            counters[backend]["split_cat_to_slices_pass"] += 1
            continue
        if len(new_cat_args) > 1 and len(new_cat_args) < len(cat_inputs):
            new_args = (new_cat_args,)
            with graph.inserting_after(cat_node):
                new_cat_node = graph.call_function(
                    torch.cat,
                    args=new_args,
                    # split and cat have the same dim
                    kwargs={"dim": split_dim},
                )
                cat_node.replace_all_uses_with(new_cat_node)
                new_cat_node.meta.update(cat_node.meta)
                # remove the cat node
                graph.erase_node(cat_node)
                remove_split_unbind_children(graph, cat_inputs)
                counters[backend]["split_cat_to_slices_pass"] += 1