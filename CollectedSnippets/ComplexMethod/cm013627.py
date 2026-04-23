def _topological_sort_passes(
    passes: list[Callable[..., Any]], constraints: list[Callable[..., Any]]
) -> list[Callable[..., Any]]:
    """
    Args
        passes: Passes that we are ordering
        constraints: Constraints applied on these passes

    Returns
        A sorted list of callables and a boolean of if a circular dependency
        existed
    """
    if len(constraints) == 0:
        return passes

    # Construct a graph mapping nodes to a list of their users
    graph: dict[Callable[..., Any], list[Callable[..., Any]]] = {p: [] for p in passes}
    indegree_map: dict[Callable[..., Any], int] = dict.fromkeys(passes, 0)
    candidates: Queue[Callable[..., Any]] = Queue()
    for a in passes:
        for b in passes:
            if a == b:
                continue

            for constraint in constraints:
                if not constraint(a, b):
                    graph[b].append(a)
                    indegree_map[a] += 1

        if indegree_map[a] == 0:
            candidates.put(a)

    visited: dict[Callable[..., Any], bool] = dict.fromkeys(passes, False)
    sorted_passes: list[Callable[..., Any]] = []

    while not candidates.empty():
        p = candidates.get()
        sorted_passes.append(p)
        visited[p] = True

        for n in graph[p]:
            if not visited[n]:
                indegree_map[n] -= 1
                if indegree_map[n] == 0:
                    candidates.put(n)

    # Check if there are unvisited nodes (aka cycles in the graph)
    cycle_passes = list(filter(lambda p: indegree_map[p] != 0, indegree_map.keys()))
    if len(cycle_passes) != 0:
        error = (
            f"Circular dependency detected within the following passes: {cycle_passes}"
        )
        raise RuntimeError(error)

    return sorted_passes