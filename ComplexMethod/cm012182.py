def efficient_conv_bn_eval_graph_transform_inlined(match: Match, *args, **kwargs):
    bn_node = match.nodes[0]
    graph = match.graph
    assert len(bn_node.args) == 8

    # We can only use efficient conv-bn for eval mode with track_running_stats
    # bn_node.args is `training`
    if bn_node.args[-3]:
        return

    # Check if the input is Conv
    input_node = bn_node.args[0]

    if input_node.op != "call_function":  # type: ignore[union-attr]
        return

    input_fn = input_node.target  # type: ignore[arg-type, union-attr]
    supported_convs = [
        torch._C._nn.linear,
        torch.conv1d,
        torch.conv2d,
        torch.conv3d,
        torch.conv_transpose1d,
        torch.conv_transpose2d,
        torch.conv_transpose3d,
    ]

    if not any(input_fn is cls for cls in supported_convs):
        return

    conv_node = input_node
    # Output of conv is used by other nodes, cannot optimize
    if len(conv_node.users) > 1:  # type: ignore[union-attr]
        return

    counters["inductor"]["efficient_conv_bn_eval"] += 1

    with graph.inserting_before(bn_node):
        # prepare args for the fused function
        bn_running_mean = bn_node.args[1]
        bn_running_var = bn_node.args[2]
        bn_weight = bn_node.args[3]
        bn_bias = bn_node.args[4]
        bn_eps = bn_node.args[7]
        assert len(conv_node.args) >= 2  # type: ignore[union-attr]
        conv_input = conv_node.args[0]  # type: ignore[union-attr]
        conv_weight = conv_node.args[1]  # type: ignore[union-attr]
        conv_bias = conv_node.args[2] if len(conv_node.args) >= 3 else None  # type: ignore[union-attr]
        conv_remaining_args = conv_node.args[3:]  # type: ignore[union-attr]
        args = (
            bn_weight,
            bn_bias,
            bn_running_mean,
            bn_running_var,
            bn_eps,
            conv_node.target,  # type: ignore[union-attr]
            conv_weight,
            conv_bias,
            conv_input,
            conv_remaining_args,
        )

        # create a new node
        new_node = graph.create_node(
            op="call_function",
            target=efficient_conv_bn_eval_decomposed,
            args=args,  # type: ignore[arg-type]
            name="efficient_conv_bn_eval",
        )

    # this node replaces the original conv + bn, and therefore
    # should replace the uses of bn_node
    bn_node.replace_all_uses_with(new_node)
    # take care of the deletion order:
    # delete bn_node first, and then conv_node
    graph.erase_node(bn_node)
    graph.erase_node(conv_node)  # type: ignore[arg-type]

    return