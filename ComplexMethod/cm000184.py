def bfs_shortest_path_distance(graph: dict, start, target) -> int:
    """Find the shortest path distance between `start` and `target` nodes.
    Args:
        graph: node/list of neighboring nodes key/value pairs.
        start: node to start search from.
        target: node to search for.
    Returns:
        Number of edges in the shortest path between `start` and `target` nodes.
        -1 if no path exists.
    Example:
        >>> bfs_shortest_path_distance(demo_graph, "G", "D")
        4
        >>> bfs_shortest_path_distance(demo_graph, "A", "A")
        0
        >>> bfs_shortest_path_distance(demo_graph, "A", "Unknown")
        -1
    """
    if not graph or start not in graph or target not in graph:
        return -1
    if start == target:
        return 0
    queue = deque([start])
    visited = set(start)
    # Keep tab on distances from `start` node.
    dist = {start: 0, target: -1}
    while queue:
        node = queue.popleft()
        if node == target:
            dist[target] = (
                dist[node] if dist[target] == -1 else min(dist[target], dist[node])
            )
        for adjacent in graph[node]:
            if adjacent not in visited:
                visited.add(adjacent)
                queue.append(adjacent)
                dist[adjacent] = dist[node] + 1
    return dist[target]