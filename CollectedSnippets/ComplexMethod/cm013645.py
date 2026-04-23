def topo_sort(nodes: NodeList) -> NodeList:
    # Stable topological sort: among nodes with no dependency between them,
    # preserve their relative order in the input list. This uses a min-heap
    # keyed by original position instead of a FIFO queue.
    indegree_map = dict.fromkeys(nodes, 0)
    position = {node: i for i, node in enumerate(nodes)}
    candidates: list[tuple[int, Node]] = []

    for node in nodes:
        for n in node.all_input_nodes:
            if n in indegree_map:
                indegree_map[node] += 1
        if indegree_map[node] == 0:
            heapq.heappush(candidates, (position[node], node))

    sorted_nodes: NodeList = []
    while candidates:
        _, node = heapq.heappop(candidates)
        sorted_nodes.append(node)

        for n in node.users:
            if n in indegree_map:
                indegree_map[n] -= 1
                if indegree_map[n] == 0:
                    heapq.heappush(candidates, (position[n], n))

    if len(nodes) != len(sorted_nodes):
        raise AssertionError(
            "topological sorted nodes doesn't have same length as input nodes"
        )

    return sorted_nodes