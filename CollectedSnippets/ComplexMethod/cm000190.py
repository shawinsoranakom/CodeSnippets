def prisms_algorithm(adjacency_list):
    """
    >>> adjacency_list = {0: [[1, 1], [3, 3]],
    ...                   1: [[0, 1], [2, 6], [3, 5], [4, 1]],
    ...                   2: [[1, 6], [4, 5], [5, 2]],
    ...                   3: [[0, 3], [1, 5], [4, 1]],
    ...                   4: [[1, 1], [2, 5], [3, 1], [5, 4]],
    ...                   5: [[2, 2], [4, 4]]}
    >>> prisms_algorithm(adjacency_list)
    [(0, 1), (1, 4), (4, 3), (4, 5), (5, 2)]
    """

    heap = Heap()

    visited = [0] * len(adjacency_list)
    nbr_tv = [-1] * len(adjacency_list)  # Neighboring Tree Vertex of selected vertex
    # Minimum Distance of explored vertex with neighboring vertex of partial tree
    # formed in graph
    distance_tv = []  # Heap of Distance of vertices from their neighboring vertex
    positions = []

    for vertex in range(len(adjacency_list)):
        distance_tv.append(sys.maxsize)
        positions.append(vertex)
        heap.node_position.append(vertex)

    tree_edges = []
    visited[0] = 1
    distance_tv[0] = sys.maxsize
    for neighbor, distance in adjacency_list[0]:
        nbr_tv[neighbor] = 0
        distance_tv[neighbor] = distance
    heap.heapify(distance_tv, positions)

    for _ in range(1, len(adjacency_list)):
        vertex = heap.delete_minimum(distance_tv, positions)
        if visited[vertex] == 0:
            tree_edges.append((nbr_tv[vertex], vertex))
            visited[vertex] = 1
            for neighbor, distance in adjacency_list[vertex]:
                if (
                    visited[neighbor] == 0
                    and distance < distance_tv[heap.get_position(neighbor)]
                ):
                    distance_tv[heap.get_position(neighbor)] = distance
                    heap.bottom_to_top(
                        distance, heap.get_position(neighbor), distance_tv, positions
                    )
                    nbr_tv[neighbor] = vertex
    return tree_edges