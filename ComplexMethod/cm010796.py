def activation_offload_sink_wait_async(fwd_module: fx.GraphModule) -> None:
    """Sink ao.wait_tensor operations for offload completion to the end of the graph.

    This allows computation to overlap with offload operations.

    NOTE: Sinking waits to the end delays GPU memory release of the source
    tensor (kept alive via the wait's keepalive arg) until the end of the
    compiled graph. For per-layer compile this is fine (one layer's worth of
    memory), but for full-model compile this means offloaded GPU tensors are
    not freed until the entire forward pass completes.
    """
    graph: fx.Graph = fwd_module.graph
    output_node: fx.Node = graph.find_nodes(op="output")[0]

    wait_nodes_to_sink: list[fx.Node] = [
        node
        for node in graph.nodes
        if node.op == "call_function"
        and node.target == torch.ops.ao.wait_tensor.default
        and isinstance(node.args[0], fx.Node)
        and node.args[0].op == "call_function"
        and node.args[0].target == torch.ops.ao.offload.default
    ]

    # prepend moves the node from its current position (no manual removal needed)
    for wait_node in wait_nodes_to_sink:
        output_node.prepend(wait_node)