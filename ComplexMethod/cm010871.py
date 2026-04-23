def sync_deallocations(gm: torch.fx.GraphModule) -> None:
    """Handles https://docs.pytorch.org/docs/stable/generated/torch.Tensor.record_stream.html#torch.Tensor.record_stream"""
    # Note: this is only needed if the last usage of a tensor is on a stream other than
    # the stream the tensor was allocated on

    # an estimated timestamp from the beginning of graph execution (assuming 0 CPU overhead)
    # I think this is fine because you should have large tensors if you're using streams
    # although perhaps I could add a constant 10us per op ahead of the first stream op?
    # a trace of all the nodes running in a given stream
    stream_to_exec_trace: dict[int | None, IndexedDict[Node, float]] = {}
    for node in gm.graph.nodes:
        if node.op == "call_function" and is_bwd_node(node):
            allocating_stream = get_stream(node)
            users = list(node.users.keys())
            if not users:
                continue
            last_user = max(user for user in users)
            if last_user.op == "output":
                continue
            side_stream = get_stream(last_user)
            if allocating_stream != side_stream:
                handle_synced_deallocation(
                    gm.graph, stream_to_exec_trace, node, last_user
                )