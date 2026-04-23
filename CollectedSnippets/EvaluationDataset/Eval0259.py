def breadth_first_search(
    level: list[int],
    parent: list[list[int]],
    max_node: int,
    graph: dict[int, list[int]],
    root: int = 1,
) -> tuple[list[int], list[list[int]]]:
    level[root] = 0
    q: Queue[int] = Queue(maxsize=max_node)
    q.put(root)
    while q.qsize() != 0:
        u = q.get()
        for v in graph[u]:
            if level[v] == -1:
                level[v] = level[u] + 1
                q.put(v)
                parent[0][v] = u
    return level, parent
