def util_hamilton_cycle(graph: list[list[int]], path: list[int], curr_ind: int) -> bool:
    if curr_ind == len(graph):
        return graph[path[curr_ind - 1]][path[0]] == 1

    for next_ver in range(len(graph)):
        if valid_connection(graph, next_ver, curr_ind, path):
            path[curr_ind] = next_ver
            if util_hamilton_cycle(graph, path, curr_ind + 1):
                return True
            path[curr_ind] = -1
    return False
