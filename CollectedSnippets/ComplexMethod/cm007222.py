def filter_vertices_from_vertex(
    vertices_ids: list[str],
    vertex_id: str,
    get_vertex_predecessors: Callable[[str], list[str]] | None = None,
    get_vertex_successors: Callable[[str], list[str]] | None = None,
    graph_dict: dict[str, Any] | None = None,
) -> set[str]:
    """Filter vertices starting from a given vertex.

    Args:
        vertices_ids: List of vertex IDs to filter
        vertex_id: ID of the vertex to start filtering from
        get_vertex_predecessors: Function to get predecessors of a vertex
        get_vertex_successors: Function to get successors of a vertex
        graph_dict: Dictionary containing graph information

    Returns:
        Set of vertex IDs that are successors of the given vertex
    """
    vertices_set = set(vertices_ids)
    if vertex_id not in vertices_set:
        return set()

    # Build predecessor map if not provided
    if get_vertex_predecessors is None:
        if graph_dict is None:
            msg = "Either get_vertex_predecessors or graph_dict must be provided"
            raise ValueError(msg)

        def get_vertex_predecessors(v):
            return graph_dict[v]["predecessors"]

    # Build successor map if not provided
    if get_vertex_successors is None:
        if graph_dict is None:
            return set()

        def get_vertex_successors(v):
            return graph_dict[v]["successors"]

    # Start with the target vertex
    filtered_vertices = {vertex_id}
    queue = deque([vertex_id])

    # Process vertices in breadth-first order
    while queue:
        current_vertex = queue.popleft()
        for successor in get_vertex_successors(current_vertex):
            if successor in vertices_set and successor not in filtered_vertices:
                filtered_vertices.add(successor)
                queue.append(successor)

    return filtered_vertices