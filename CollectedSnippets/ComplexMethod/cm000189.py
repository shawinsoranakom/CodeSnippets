def strongly_connected_components(graph: dict[int, list[int]]) -> list[list[int]]:
    """
    This function takes graph as a parameter
    and then returns the list of strongly connected components
    >>> strongly_connected_components(test_graph_1)
    [[0, 1, 2], [3], [4]]
    >>> strongly_connected_components(test_graph_2)
    [[0, 2, 1], [3, 5, 4]]
    """

    visited = len(graph) * [False]
    reversed_graph: dict[int, list[int]] = {vert: [] for vert in range(len(graph))}

    for vert, neighbours in graph.items():
        for neighbour in neighbours:
            reversed_graph[neighbour].append(vert)

    order = []
    for i, was_visited in enumerate(visited):
        if not was_visited:
            order += topology_sort(graph, i, visited)

    components_list = []
    visited = len(graph) * [False]

    for i in range(len(graph)):
        vert = order[len(graph) - i - 1]
        if not visited[vert]:
            component = find_components(reversed_graph, vert, visited)
            components_list.append(component)

    return components_list