def is_valid_cat_splitwithsizes(match):
    cat_nodes = filter_nodes(match.nodes, aten.cat)
    split_nodes = filter_nodes(match.nodes, aten.split_with_sizes)
    if len(split_nodes) != 1 or len(cat_nodes) != 1:
        return False
    split_node, cat_node = split_nodes[0], cat_nodes[0]

    # the cat node has other users: can't eliminate
    if len(cat_node.users) > 1:
        return False

    # the dim of the cat and split should match
    dim = get_arg_value(split_node, 2, "dim")
    if dim != get_arg_value(cat_node, 1, "dim"):
        return False

    cat_inputs = list(get_arg_value(cat_node, 0))
    split_sizes = get_arg_value(split_node, 1, "split_sizes")
    # the number of input tensors in cat and the
    # length of the split sizes should match
    if len(cat_inputs) != len(split_sizes):
        return False

    for cat_input, split_size in zip(cat_inputs, split_sizes):
        # each cat input tensor's size along dim
        # should match the corresponding split size
        if "val" not in cat_input.meta:
            return False
        cat_input_size = cat_input.meta["val"].size(dim)
        if cat_input_size != split_size:
            return False

    return True