def assign_memory_planning_info_for_scheduler_nodes(
    nodes: list[BaseSchedulerNode],
    name_to_fused_node: dict[str, BaseSchedulerNode],
    name_to_buf: dict[str, SchedulerBuffer],
    name_to_freeable_input_buf: dict[str, FreeableInputBuffer],
) -> None:
    """
    Assign to each scheduler node its predecessor and successor nodes.
    """

    node_to_pred_nodes: dict[BaseSchedulerNode, OrderedSet[BaseSchedulerNode]] = (
        collections.defaultdict(OrderedSet)
    )
    node_to_succ_nodes: dict[BaseSchedulerNode, OrderedSet[BaseSchedulerNode]] = {}
    node_to_pred_buffers: dict[
        BaseSchedulerNode, OrderedSet[SchedulerBuffer | FreeableInputBuffer]
    ] = collections.defaultdict(OrderedSet)

    # collect all predecessors using existing successor mappings
    for node in nodes:
        succ_nodes = OrderedSet(
            succ_node
            for buffer in node.get_outputs()
            for succ_node in buffer.mpi_buffer.succ_nodes_for_ordering
        )
        node_to_succ_nodes[node] = succ_nodes

        # For each successor, add current node as its predecessor
        for succ_node in succ_nodes:
            node_to_pred_nodes[succ_node].add(node)

        # For each output buffer, add it as predecessor to its successor nodes
        # Use succ_nodes (not succ_nodes_for_ordering) since pred_buffers is used
        # for memory lifetime tracking, not ordering
        for buffer in node.get_outputs():
            for succ_node in buffer.mpi_buffer.succ_nodes:
                node_to_pred_buffers[succ_node].add(buffer)

    for freeable_buffer in name_to_freeable_input_buf.values():
        for succ_node in freeable_buffer.mpi_buffer.succ_nodes:
            node_to_pred_buffers[succ_node].add(freeable_buffer)

    # Second pass: assign memory planning info using completed predecessor mappings
    for index, node in enumerate(nodes):
        size_alloc = sum(buffer.mpi_buffer.size_alloc for buffer in node.get_outputs())
        succ_nodes = node_to_succ_nodes[node]
        pred_nodes = node_to_pred_nodes[node]

        # make sure we do not make node a successor or predecessor of itself
        succ_nodes.discard(node)
        pred_nodes.discard(node)

        node.mpi_node = MemoryPlanningInfoForNode(
            index=index,
            size=size_alloc,
            pred_buffers=node_to_pred_buffers[node],
            pred_nodes=node_to_pred_nodes[node],
            succ_nodes=succ_nodes,
        )