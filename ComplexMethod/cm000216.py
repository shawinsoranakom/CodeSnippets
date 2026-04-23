def prims_algo[T](
    graph: GraphUndirectedWeighted[T],
) -> tuple[dict[T, int], dict[T, T | None]]:
    """
    >>> graph = GraphUndirectedWeighted()

    >>> graph.add_edge("a", "b", 3)
    >>> graph.add_edge("b", "c", 10)
    >>> graph.add_edge("c", "d", 5)
    >>> graph.add_edge("a", "c", 15)
    >>> graph.add_edge("b", "d", 100)

    >>> dist, parent = prims_algo(graph)

    >>> abs(dist["a"] - dist["b"])
    3
    >>> abs(dist["d"] - dist["b"])
    15
    >>> abs(dist["a"] - dist["c"])
    13
    """
    # prim's algorithm for minimum spanning tree
    dist: dict[T, int] = dict.fromkeys(graph.connections, maxsize)
    parent: dict[T, T | None] = dict.fromkeys(graph.connections)

    priority_queue: MinPriorityQueue[T] = MinPriorityQueue()
    for node, weight in dist.items():
        priority_queue.push(node, weight)

    if priority_queue.is_empty():
        return dist, parent

    # initialization
    node = priority_queue.extract_min()
    dist[node] = 0
    for neighbour in graph.connections[node]:
        if dist[neighbour] > dist[node] + graph.connections[node][neighbour]:
            dist[neighbour] = dist[node] + graph.connections[node][neighbour]
            priority_queue.update_key(neighbour, dist[neighbour])
            parent[neighbour] = node

    # running prim's algorithm
    while not priority_queue.is_empty():
        node = priority_queue.extract_min()
        for neighbour in graph.connections[node]:
            if dist[neighbour] > dist[node] + graph.connections[node][neighbour]:
                dist[neighbour] = dist[node] + graph.connections[node][neighbour]
                priority_queue.update_key(neighbour, dist[neighbour])
                parent[neighbour] = node
    return dist, parent