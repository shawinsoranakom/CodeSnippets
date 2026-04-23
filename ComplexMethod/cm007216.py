def sort_up_to_vertex(
    graph: dict[str, dict[str, list[str]]],
    vertex_id: str,
    *,
    parent_node_map: dict[str, str | None] | None = None,
    is_start: bool = False,
) -> list[str]:
    """Cuts the graph up to a given vertex and sorts the resulting subgraph."""
    try:
        stop_or_start_vertex = graph[vertex_id]
    except KeyError as e:
        if parent_node_map is None:
            msg = "Parent node map is required to find the root of a group node"
            raise ValueError(msg) from e
        vertex_id = get_root_of_group_node(graph=graph, vertex_id=vertex_id, parent_node_map=parent_node_map)
        if vertex_id not in graph:
            msg = f"Vertex {vertex_id} not found into graph"
            raise ValueError(msg) from e
        stop_or_start_vertex = graph[vertex_id]

    visited, excluded = set(), set()
    stack = [vertex_id]
    stop_predecessors = set(stop_or_start_vertex["predecessors"])

    while stack:
        current_id = stack.pop()
        if current_id in visited or current_id in excluded:
            continue

        visited.add(current_id)
        current_vertex = graph[current_id]

        stack.extend(current_vertex["predecessors"])

        if current_id == vertex_id or (current_id not in stop_predecessors and is_start):
            for successor_id in current_vertex["successors"]:
                if is_start:
                    stack.append(successor_id)
                else:
                    excluded.add(successor_id)
                for succ_id in get_successors(graph, successor_id):
                    if is_start:
                        stack.append(succ_id)
                    else:
                        excluded.add(succ_id)

    return list(visited)