def layered_topological_sort(
    vertices_ids: set[str],
    in_degree_map: dict[str, int],
    successor_map: dict[str, list[str]],
    predecessor_map: dict[str, list[str]],
    start_id: str | None = None,
    cycle_vertices: set[str] | None = None,
    is_input_vertex: Callable[[str], bool] | None = None,  # noqa: ARG001
    *,
    is_cyclic: bool = False,
) -> list[list[str]]:
    """Performs a layered topological sort of the vertices in the graph.

    Args:
        vertices_ids: Set of vertex IDs to sort
        in_degree_map: Map of vertex IDs to their in-degree
        successor_map: Map of vertex IDs to their successors
        predecessor_map: Map of vertex IDs to their predecessors
        is_cyclic: Whether the graph is cyclic
        start_id: ID of the start vertex (if any)
        cycle_vertices: Set of vertices that form a cycle
        is_input_vertex: Function to check if a vertex is an input vertex

    Returns:
        List of layers, where each layer is a list of vertex IDs
    """
    # Queue for vertices with no incoming edges
    cycle_vertices = cycle_vertices or set()
    in_degree_map = in_degree_map.copy()

    if is_cyclic and all(in_degree_map.values()):
        # This means we have a cycle because all vertex have in_degree_map > 0
        # because of this we set the queue to start on the start_id if it exists
        if start_id is not None:
            queue = deque([start_id])
            # Reset in_degree for start_id to allow cycle traversal
            in_degree_map[start_id] = 0
        else:
            # Find the chat input component
            chat_input = find_start_component_id(vertices_ids)
            if chat_input is None:
                # If no input component is found, start with any vertex
                queue = deque([next(iter(vertices_ids))])
                in_degree_map[next(iter(vertices_ids))] = 0
            else:
                queue = deque([chat_input])
                # Reset in_degree for chat_input to allow cycle traversal
                in_degree_map[chat_input] = 0
    else:
        # Start with vertices that have no incoming edges or are input vertices
        queue = deque(
            vertex_id
            for vertex_id in vertices_ids
            if in_degree_map[vertex_id] == 0
            # We checked if it is input but that caused the TextInput to be at the start
            # or (is_input_vertex and is_input_vertex(vertex_id))
        )

    layers: list[list[str]] = []
    visited = set()
    cycle_counts = dict.fromkeys(vertices_ids, 0)
    current_layer = 0

    # Process the first layer separately to avoid duplicates
    if queue:
        layers.append([])  # Start the first layer
        first_layer_vertices = set()
        layer_size = len(queue)
        for _ in range(layer_size):
            vertex_id = queue.popleft()
            if vertex_id not in first_layer_vertices:
                first_layer_vertices.add(vertex_id)
                visited.add(vertex_id)
                cycle_counts[vertex_id] += 1
                layers[current_layer].append(vertex_id)

            for neighbor in successor_map[vertex_id]:
                # only vertices in `vertices_ids` should be considered
                # because vertices by have been filtered out
                # in a previous step. All dependencies of theirs
                # will be built automatically if required
                if neighbor not in vertices_ids:
                    continue

                in_degree_map[neighbor] -= 1  # 'remove' edge
                if in_degree_map[neighbor] == 0:
                    queue.append(neighbor)

                # if > 0 it might mean not all predecessors have added to the queue
                # so we should process the neighbors predecessors
                elif in_degree_map[neighbor] > 0:
                    for predecessor in predecessor_map[neighbor]:
                        if (
                            predecessor not in queue
                            and predecessor not in first_layer_vertices
                            and (in_degree_map[predecessor] == 0 or predecessor in cycle_vertices)
                        ):
                            queue.append(predecessor)

        current_layer += 1  # Next layer

    # Process remaining layers normally, allowing cycle vertices to appear multiple times
    while queue:
        layers.append([])  # Start a new layer
        layer_size = len(queue)
        for _ in range(layer_size):
            vertex_id = queue.popleft()
            if vertex_id not in visited or (is_cyclic and cycle_counts[vertex_id] < MAX_CYCLE_APPEARANCES):
                if vertex_id not in visited:
                    visited.add(vertex_id)
                cycle_counts[vertex_id] += 1
                layers[current_layer].append(vertex_id)

            for neighbor in successor_map[vertex_id]:
                # only vertices in `vertices_ids` should be considered
                # because vertices by have been filtered out
                # in a previous step. All dependencies of theirs
                # will be built automatically if required
                if neighbor not in vertices_ids:
                    continue

                in_degree_map[neighbor] -= 1  # 'remove' edge
                if in_degree_map[neighbor] == 0 and neighbor not in visited:
                    queue.append(neighbor)
                    # # If this is a cycle vertex, reset its in_degree to allow it to appear again
                    # if neighbor in cycle_vertices and neighbor in visited:
                    #     in_degree_map[neighbor] = len(predecessor_map[neighbor])

                # if > 0 it might mean not all predecessors have added to the queue
                # so we should process the neighbors predecessors
                elif in_degree_map[neighbor] > 0:
                    for predecessor in predecessor_map[neighbor]:
                        if predecessor not in queue and (
                            predecessor not in visited
                            or (is_cyclic and cycle_counts[predecessor] < MAX_CYCLE_APPEARANCES)
                        ):
                            queue.append(predecessor)

        current_layer += 1  # Next layer

    # Remove empty layers
    return [layer for layer in layers if layer]