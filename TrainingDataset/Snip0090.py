def hamilton_cycle(graph: list[list[int]], start_index: int = 0) -> list[int]:

    path = [-1] * (len(graph) + 1)
    path[0] = path[-1] = start_index
    return path if util_hamilton_cycle(graph, path, 1) else []
