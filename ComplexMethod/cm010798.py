def activation_offload_sink_wait(fwd_module: fx.GraphModule) -> None:
    """
    Sink wait_event operations for offload completion to the end of the graph.

    This function identifies wait_event nodes for offload completion and moves them
    to the end of the graph, allowing computation to overlap with offload operations.

    Args:
        fwd_module: Forward module graph
    """
    graph: fx.Graph = fwd_module.graph
    nodes_list: list[fx.Node] = list(graph.nodes)
    node_to_idx: dict[fx.Node, int] = {node: idx for idx, node in enumerate(nodes_list)}

    # Find all CPU offload device_put nodes
    offload_nodes: list[fx.Node] = [
        node
        for node in graph.find_nodes(
            op="call_function", target=torch.ops.prims.device_put.default
        )
        if CPU_OFFLOAD_PREFIX in node.name
    ]

    # Collect all wait_event nodes that need to be moved
    wait_nodes_to_sink: list[fx.Node] = []
    for offload_node in offload_nodes:
        offload_idx: int = node_to_idx[offload_node]
        wait_event_node: fx.Node = nodes_list[offload_idx + 3]

        # Validate it's actually a wait_event node
        if not (
            wait_event_node.op == "call_function"
            and wait_event_node.target == torch.ops.streams.wait_event.default
        ):
            raise ValueError(
                f"Expected wait_event node three positions after {offload_node.name}"
            )

        wait_nodes_to_sink.append(wait_event_node)

    # Find the output node, and move all wait_event nodes to just before the output node
    output_node: fx.Node = graph.find_nodes(op="output")[0]
    for wait_node in wait_nodes_to_sink:
        output_node.prepend(wait_node)