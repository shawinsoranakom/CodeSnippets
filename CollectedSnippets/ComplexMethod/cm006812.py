def get_loop_body_vertices(
    vertex: "Vertex",
    graph: "Graph",
    get_incoming_edge_by_target_param_fn,
    loop_output_name: str = "item",
    feedback_input_name: str | None = None,
) -> set[str]:
    """Get all vertex IDs that are part of the loop body.

    Uses BFS to traverse from the loop's output to the vertex
    that feeds back to the loop's input, then includes all
    predecessors of vertices in the loop body.

    Args:
        vertex: The loop component's vertex
        graph: The graph containing the loop
        get_incoming_edge_by_target_param_fn: Function to get incoming edge by target param
        loop_output_name: Name of the output that starts the loop body
            (default: "item" for Loop, use "loop" for WhileLoop)
        feedback_input_name: Name of the input that receives feedback
            (default: same as loop_output_name)

    Returns:
        Set of vertex IDs that form the loop body
    """
    if feedback_input_name is None:
        feedback_input_name = loop_output_name

    # Find where the loop body starts (edges from loop output)
    start_edges = [e for e in vertex.outgoing_edges if e.source_handle.name == loop_output_name]
    if not start_edges:
        return set()

    # Find where it ends (vertex feeding back to loop input)
    end_vertex_id = get_incoming_edge_by_target_param_fn(feedback_input_name)
    if not end_vertex_id:
        return set()

    # BFS from start vertices, collecting all vertices until end_vertex
    loop_body = set()
    queue = deque([e.target_id for e in start_edges])
    visited = set()

    while queue:
        current = queue.popleft()
        if current in visited:
            continue
        visited.add(current)
        loop_body.add(current)

        # Don't traverse beyond the end vertex
        if current == end_vertex_id:
            continue

        # Add successors
        for successor_id in graph.successor_map.get(current, []):
            if successor_id not in visited:
                queue.append(successor_id)

    # Now recursively include all predecessors of vertices in the loop body
    # This ensures we include all dependencies like LLM models
    # We need to find predecessors by looking at successor_map in reverse
    def add_all_predecessors(vertex_id: str, visited_predecessors: set[str]) -> None:
        """Recursively add all predecessors of a vertex."""
        # Find predecessors by checking which vertices have this vertex as a successor
        for potential_pred_id, successors in graph.successor_map.items():
            if (
                vertex_id in successors
                and potential_pred_id != vertex.id
                and potential_pred_id not in visited_predecessors
            ):
                visited_predecessors.add(potential_pred_id)
                loop_body.add(potential_pred_id)
                # Recursively add predecessors of this predecessor
                add_all_predecessors(potential_pred_id, visited_predecessors)

    # Track visited predecessors to avoid infinite loops
    visited_predecessors: set[str] = set()

    # Add all predecessors for each vertex in the loop body
    for body_vertex_id in list(loop_body):  # Use list() to avoid modifying set during iteration
        add_all_predecessors(body_vertex_id, visited_predecessors)

    return loop_body