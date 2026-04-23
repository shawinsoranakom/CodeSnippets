def merge_select_cat_aten(match: Match, *args, **kwargs):
    graph = match.graph
    node = match.nodes[0]
    node_input = get_arg_value(node, 0, "tensors")
    # get the select nodes from the node
    select_nodes = list(node_input.users.keys())
    for cat_node in list(node.users.keys()):
        if cat_node.target is torch.ops.aten.cat.default:
            cat_dim = get_arg_value(cat_node, 1, "dim")
            cat_inputs = get_arg_value(cat_node, 0, "tensors")
            # check all select nodes has same slice dim
            if not all(
                select_node.args[1] == select_nodes[0].args[1]
                for select_node in select_nodes
            ):
                continue
            # We only consider the case where selece slice dim and cat node has same dim
            if select_nodes[0].args[1] != cat_dim:
                continue
            if not is_node_meta_valid(cat_node):
                continue
            # check the cat node has consecutive indices
            indices = [select.args[2] for select in cat_node.args[0]]  # type: ignore[union-attr]
            if (
                not is_sorted_and_consecutive(indices)  # type: ignore[arg-type]
                or len(select_nodes) != len(cat_inputs)
            ):
                continue
            # check all the select nodes can be merged to the cat node input
            if len(indices) != select_nodes[0].args[0].meta["val"].shape[cat_dim]:  # type: ignore[union-attr]
                continue
            # reshape the node input to be the same shape as the cat node
            with graph.inserting_before(node):
                view_node = graph.call_function(
                    torch.ops.aten.view.default,
                    args=(node_input, cat_node.meta["val"].shape),
                )
            # replace the node input with the new node
            cat_node.replace_all_uses_with(view_node)
            view_node.meta.update(cat_node.meta)
            # remove the cat node
            graph.erase_node(cat_node)
            for select_node in select_nodes:
                if len(select_node.users) == 0:
                    graph.erase_node(select_node)
            counters[backend]["select_cat_aten_pass"] += 1