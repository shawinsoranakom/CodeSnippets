def insert_backward_syncs(gm: torch.fx.GraphModule) -> None:
    """Inserts stream syncs for backward nodes if consumer and producer are on different streams"""
    node_to_wait_event_ind: dict[Node, int] = {}
    for node in gm.graph.nodes:
        if node.op == "call_function" and is_bwd_node(node):
            flat_args = _get_flat_args(node, {})
            cur_node_stream = get_stream(node)

            for arg in flat_args:
                if arg.op == "call_function" and is_bwd_node(arg):
                    arg_stream = get_stream(arg)
                    if arg_stream != cur_node_stream and get_device(arg).type != "cpu":
                        insert_sync(gm.graph, node, arg, node_to_wait_event_ind)