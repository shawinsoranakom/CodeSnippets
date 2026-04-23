def bfs_shortest_path_distance(graph: dict, start, target) -> int:
    if not graph or start not in graph or target not in graph:
        return -1
    if start == target:
        return 0
    queue = deque([start])
    visited = set(start)
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
