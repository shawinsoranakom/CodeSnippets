def stable_topological_sort(gm: torch.fx.GraphModule) -> torch.fx.GraphModule:
    """
    Replace the graph of the given GraphModule with one that contains the same nodes as the
    original, but in topologically sorted order while preserving the original node order
    as much as possible.

    This function performs a stable topological sort where nodes appear in an order that:
    1. Respects data dependencies (topological ordering)
    2. Preserves the original node order when there are no dependency constraints

    The algorithm uses Kahn's algorithm with a priority queue: nodes with all dependencies
    satisfied are added to a min-heap, ordered by their original position. This ensures
    we always process the earliest node in the original order among ready nodes.

    Arguments:
        gm: The graph module to topologically sort. It is modified in-place.

    Returns:
        The graph module in-place sorted
    """
    indeg = dict.fromkeys(gm.graph.nodes, 0)
    new_graph = torch.fx.Graph()

    # Build node to original index mapping
    node_to_id: dict[torch.fx.Node, int] = {
        node: idx for idx, node in enumerate(gm.graph.nodes)
    }

    # Track how many unfulfilled dependencies each node has
    for node in gm.graph.nodes:
        for user in node.users:
            indeg[user] += 1

    # Priority queue: (original_index, node)
    # Use min-heap to always process the node with smallest original index
    ready_queue: list[tuple[int, torch.fx.Node]] = []
    for node in gm.graph.nodes:
        if indeg[node] == 0:
            heapq.heappush(ready_queue, (node_to_id[node], node))

    env: dict[torch.fx.Node, torch.fx.Node] = {}

    # Process nodes
    while ready_queue:
        # Pop node with smallest original index
        _, cur = heapq.heappop(ready_queue)
        env[cur] = new_graph.node_copy(cur, lambda x: env[x])

        # Update in-degrees and add newly ready nodes
        for user in cur.users:
            indeg[user] -= 1
            if indeg[user] == 0:
                heapq.heappush(ready_queue, (node_to_id[user], user))

    # Check if all nodes were processed
    if len(new_graph.nodes) != len(gm.graph.nodes):
        raise AssertionError(
            f"Input graph has cycles, unable to add {[node for node in indeg if indeg[node] != 0]}"
        )

    new_graph._codegen = gm.graph._codegen
    gm.graph = new_graph
    return gm