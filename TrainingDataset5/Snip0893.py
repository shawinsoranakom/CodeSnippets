def depth_first_search(graph: dict, start: str) -> set[str]:
    explored, stack = set(start), [start]

    while stack:
        v = stack.pop()
        explored.add(v)
        for adj in reversed(graph[v]):
            if adj not in explored:
                stack.append(adj)
    return explored
