def merge_unbind_stack_aten(match: Match, *args, **kwargs):
    node = match.nodes[-1]
    graph = match.graph
    # pyre-fixme[6]
    unsqueeze_nodes = list(node.args[0])  # type: ignore[arg-type]
    cat_dim = get_arg_value(node, 1, "dim")
    # check the unsqueeze nodes come from the select nodes
    if not all(
        # pyrefly: ignore [bad-argument-type]
        get_arg_value(unsqueeze_node, 0, "input").target is torch.ops.aten.select
        for unsqueeze_node in unsqueeze_nodes
    ):
        return
    select_nodes = [
        # pyrefly: ignore [bad-argument-type]
        get_arg_value(unsqueeze_node, 0, "input")
        for unsqueeze_node in unsqueeze_nodes
    ]
    parent_of_select_node = get_arg_value(select_nodes[0], 0, "input")
    # check the target of select_nodes are the same
    if not all(
        select_node.target is torch.ops.aten.select for select_node in select_nodes
    ):
        return
    # check the select nodes come from the same parent node
    if not all(
        get_arg_value(select_node, 0, "input") == parent_of_select_node
        for select_node in select_nodes
    ):
        return
    if len(unsqueeze_nodes) != len(select_nodes):
        return
    # check the select nodes have the same dim
    if not all(
        get_arg_value(select_node, 1, "dim") == cat_dim for select_node in select_nodes
    ):
        return
    # check the select nodes have consecutive indices starting from 0
    if get_arg_value(select_nodes[0], 2, "index") != 0 or not is_sorted_and_consecutive(
        [get_arg_value(select_node, 2, "index") for select_node in select_nodes]
    ):
        return
    # check the users of parent of select node only from unsqueeze nodes that go to the cat node
    # we simply check the number of users of the parent of select node
    if len(parent_of_select_node.users.keys()) != len(node.args[0]):  # type: ignore[arg-type]
        return
    node.replace_all_uses_with(parent_of_select_node)
    graph.erase_node(node)
    for unsqueeze_node in unsqueeze_nodes:
        # pyrefly: ignore [bad-argument-type]
        graph.erase_node(unsqueeze_node)
    for select_node in select_nodes:
        if len(select_node.users) == 0:
            graph.erase_node(select_node)
    counters[backend]["unbind_stack_aten_pass"] += 1