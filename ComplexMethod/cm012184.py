def efficient_conv_bn_eval_graph_transform(match: Match, *args, **kwargs):
    # We matched a BN node
    bn_node = match.nodes[0]
    graph = match.graph
    gm = graph.owning_module
    bn_mod = getattr(gm, bn_node.target)  # type: ignore[arg-type]

    # We can only use efficient conv-bn for eval mode with track_running_stats
    if not bn_mod.track_running_stats or bn_mod.training:
        return

    # Check if the input is Conv
    if bn_node.args:
        input_node = bn_node.args[0]
    else:
        input_node = bn_node.kwargs["input"]
    if input_node.op != "call_module":  # type: ignore[union-attr]
        return
    if not hasattr(gm, input_node.target):  # type: ignore[arg-type, union-attr]
        return
    input_mod = getattr(gm, input_node.target)  # type: ignore[arg-type, union-attr]
    supported_convs = [
        nn.Linear,
        nn.Conv1d,
        nn.Conv2d,
        nn.Conv3d,
        nn.ConvTranspose1d,
        nn.ConvTranspose2d,
        nn.ConvTranspose3d,
    ]
    if not any(isinstance(input_mod, cls) for cls in supported_convs):
        return
    conv_node = input_node
    # Output of conv is used by other nodes, cannot optimize
    if len(conv_node.users) > 1:  # type: ignore[union-attr]
        return

    # Find a pair of conv and bn computation nodes to optimize.
    counters["inductor"]["efficient_conv_bn_eval"] += 1

    with graph.inserting_before(conv_node):  # type: ignore[arg-type]
        # create `get_attr` node to access modules
        # note that we directly call `create_node` to fill the `name`
        # argument. `graph.get_attr` and
        # `graph.call_function` does not allow the `name` argument.
        conv_get_node = graph.create_node(
            op="get_attr",
            target=conv_node.target,  # type: ignore[union-attr]
            name="get_conv",
        )
        bn_get_node = graph.create_node(
            op="get_attr", target=bn_node.target, name="get_bn"
        )
        if conv_node.args:  # type: ignore[union-attr]
            conv_input = conv_node.args[0]  # type: ignore[union-attr]
        else:
            conv_input = conv_node.kwargs["input"]  # type: ignore[union-attr]
        # prepare args for the fused function
        args = (bn_get_node, conv_get_node, conv_input)
        # create a new node
        new_node = graph.create_node(
            op="call_function",
            target=efficient_conv_bn_eval,
            args=args,
            name="efficient_conv_bn_eval",
        )
    # this node replaces the original conv + bn, and therefore
    # should replace the uses of bn_node
    bn_node.replace_all_uses_with(new_node)
    # take care of the deletion order:
    # delete bn_node first, and then conv_node
    graph.erase_node(bn_node)
    graph.erase_node(conv_node)