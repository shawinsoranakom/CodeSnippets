def breadth_first_search_with_deque(graph: dict, start: str) -> list[str]:
    visited = {start}
    result = [start]
    queue = deque([start])
    while queue:
        v = queue.popleft()
        for child in graph[v]:
            if child not in visited:
                visited.add(child)
                result.append(child)
                queue.append(child)
    return result
