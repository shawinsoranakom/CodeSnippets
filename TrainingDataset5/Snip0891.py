def connected_components(graph: dict) -> list:
    graph_size = len(graph)
    visited = graph_size * [False]
    components_list = []

    for i in range(graph_size):
        if not visited[i]:
            i_connected = dfs(graph, i, visited)
            components_list.append(i_connected)

    return components_list
