def remove_split_with_size_one(match: Match, *args, **kwargs):
    graph = match.graph
    split_node = match.nodes[0]
    split_input, split_size, split_dim = _get_split_args_default(split_node)
    if split_input is None or split_dim is None or split_size is None:
        log.debug("couldn't find split args")
        return
    if not is_node_meta_valid(split_node):
        log.debug("example value absent for node: %s", split_node)
        return
    assert isinstance(split_node.meta["example_value"], (list, tuple))
    split_sections = [t.size()[split_dim] for t in split_node.meta["example_value"]]

    if any(isinstance(section, torch.SymInt) for section in split_sections):
        # TODO dynamic_shapes with assume_static_by_default=False fails while AOT Autograd tracing.
        return
    # remove the dummy split whose split sections size is one
    # theoretically nodes with no users should be removed, but we have seen the corner case
    # thus we add its users check to walk around the StopIteration error.
    if len(split_sections) == 1 and len(split_node.users.keys()) > 0:
        # find the grand children of the split_node
        next_users = find_next_users(split_node)
        user = next(iter(split_node.users.keys()))
        # replace the users of grand child node with the input node
        for next_user in next_users:
            next_user.replace_input_with(user, split_input)
        # erase the split node and its child
        graph.erase_node(user)
        graph.erase_node(split_node)
        counters[backend]["remove_split_with_size_one_pass"] += 1