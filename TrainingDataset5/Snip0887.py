def is_bipartite_bfs(graph: dict[int, list[int]]) -> bool:
    visited: defaultdict[int, int] = defaultdict(lambda: -1)
    for node in graph:
        if visited[node] == -1:
            queue: deque[int] = deque()
            queue.append(node)
            visited[node] = 0
            while queue:
                curr_node = queue.popleft()
                if curr_node not in graph:
                    continue
                for neighbor in graph[curr_node]:
                    if visited[neighbor] == -1:
                        visited[neighbor] = 1 - visited[curr_node]
                        queue.append(neighbor)
                    elif visited[neighbor] == visited[curr_node]:
                        return False
    return True
