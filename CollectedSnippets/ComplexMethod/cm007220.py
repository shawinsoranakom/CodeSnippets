def get_sorted_vertices(
    vertices_ids: list[str],
    cycle_vertices: set[str],
    stop_component_id: str | None = None,
    start_component_id: str | None = None,
    graph_dict: dict[str, Any] | None = None,
    in_degree_map: dict[str, int] | None = None,
    successor_map: dict[str, list[str]] | None = None,
    predecessor_map: dict[str, list[str]] | None = None,
    is_input_vertex: Callable[[str], bool] | None = None,
    get_vertex_predecessors: Callable[[str], list[str]] | None = None,
    get_vertex_successors: Callable[[str], list[str]] | None = None,
    *,
    is_cyclic: bool = False,
) -> tuple[list[str], list[list[str]]]:
    """Get sorted vertices in a graph.

    Args:
        vertices_ids: List of vertex IDs to sort
        cycle_vertices: Set of vertices that form a cycle
        stop_component_id: ID of the stop component (if any)
        start_component_id: ID of the start component (if any)
        graph_dict: Dictionary containing graph information
        in_degree_map: Map of vertex IDs to their in-degree
        successor_map: Map of vertex IDs to their successors
        predecessor_map: Map of vertex IDs to their predecessors
        is_input_vertex: Function to check if a vertex is an input vertex
        get_vertex_predecessors: Function to get predecessors of a vertex
        get_vertex_successors: Function to get successors of a vertex
        is_cyclic: Whether the graph is cyclic

    Returns:
        Tuple of (first layer vertices, remaining layer vertices)
    """
    # Handle cycles by converting stop to start
    if stop_component_id in cycle_vertices:
        start_component_id = stop_component_id
        stop_component_id = None

    # Build in_degree_map if not provided
    if in_degree_map is None:
        in_degree_map = {}
        for vertex_id in vertices_ids:
            if get_vertex_predecessors is not None:
                in_degree_map[vertex_id] = len(get_vertex_predecessors(vertex_id))
            else:
                in_degree_map[vertex_id] = 0

    # Build successor_map if not provided
    if successor_map is None:
        successor_map = {}
        for vertex_id in vertices_ids:
            if get_vertex_successors is not None:
                successor_map[vertex_id] = get_vertex_successors(vertex_id)
            else:
                successor_map[vertex_id] = []

    # Build predecessor_map if not provided
    if predecessor_map is None:
        predecessor_map = {}
        for vertex_id in vertices_ids:
            if get_vertex_predecessors is not None:
                predecessor_map[vertex_id] = get_vertex_predecessors(vertex_id)
            else:
                predecessor_map[vertex_id] = []

    # If we have a stop component, we need to filter out all vertices
    # that are not predecessors of the stop component
    if stop_component_id is not None:
        filtered_vertices = filter_vertices_up_to_vertex(
            vertices_ids,
            stop_component_id,
            get_vertex_predecessors=get_vertex_predecessors,
            get_vertex_successors=get_vertex_successors,
            graph_dict=graph_dict,
        )
        vertices_ids = list(filtered_vertices)

    # If we have a start component, we need to filter out unconnected vertices
    # but keep vertices that are connected to the graph even if not reachable from start
    if start_component_id is not None:
        # First get all vertices reachable from start
        reachable_vertices = filter_vertices_from_vertex(
            vertices_ids,
            start_component_id,
            get_vertex_predecessors=get_vertex_predecessors,
            get_vertex_successors=get_vertex_successors,
            graph_dict=graph_dict,
        )
        # Then get all vertices that can reach any reachable vertex
        connected_vertices = set()
        for vertex in reachable_vertices:
            connected_vertices.update(
                filter_vertices_up_to_vertex(
                    vertices_ids,
                    vertex,
                    get_vertex_predecessors=get_vertex_predecessors,
                    get_vertex_successors=get_vertex_successors,
                    graph_dict=graph_dict,
                )
            )
        vertices_ids = list(connected_vertices)

    # Get the layers
    layers = layered_topological_sort(
        vertices_ids=set(vertices_ids),
        in_degree_map=in_degree_map,
        successor_map=successor_map,
        predecessor_map=predecessor_map,
        start_id=start_component_id,
        is_input_vertex=is_input_vertex,
        cycle_vertices=cycle_vertices,
        is_cyclic=is_cyclic,
    )

    # Split into first layer and remaining layers
    if not layers:
        return [], []

    first_layer = layers[0]
    remaining_layers = layers[1:]

    # If we have a stop component, we need to filter out all vertices
    # that are not predecessors of the stop component
    if stop_component_id is not None and remaining_layers and stop_component_id not in remaining_layers[-1]:
        remaining_layers[-1].append(stop_component_id)

    # Sort chat inputs first and sort each layer by dependencies
    all_layers = [first_layer, *remaining_layers]
    if get_vertex_predecessors is not None and start_component_id is None:
        all_layers = sort_chat_inputs_first(all_layers, get_vertex_predecessors)
    if get_vertex_successors is not None:
        all_layers = sort_layer_by_dependency(all_layers, get_vertex_successors)

    if not all_layers:
        return [], []

    return all_layers[0], all_layers[1:]