def valid_connection(
    graph: list[list[int]], next_ver: int, curr_ind: int, path: list[int]
) -> bool:

    if graph[path[curr_ind - 1]][next_ver] == 0:
        return False

    return not any(vertex == next_ver for vertex in path)
