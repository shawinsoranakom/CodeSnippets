def bidirectional_dij(
    source: str, destination: str, graph_forward: dict, graph_backward: dict
) -> int:
    shortest_path_distance = -1

    visited_forward = set()
    visited_backward = set()
    cst_fwd = {source: 0}
    cst_bwd = {destination: 0}
    parent_forward = {source: None}
    parent_backward = {destination: None}
    queue_forward: PriorityQueue[Any] = PriorityQueue()
    queue_backward: PriorityQueue[Any] = PriorityQueue()

    shortest_distance = np.inf

    queue_forward.put((0, source))
    queue_backward.put((0, destination))

    if source == destination:
        return 0

    while not queue_forward.empty() and not queue_backward.empty():
        _, v_fwd = queue_forward.get()
        visited_forward.add(v_fwd)

        _, v_bwd = queue_backward.get()
        visited_backward.add(v_bwd)

        shortest_distance = pass_and_relaxation(
            graph_forward,
            v_fwd,
            visited_forward,
            visited_backward,
            cst_fwd,
            cst_bwd,
            queue_forward,
            parent_forward,
            shortest_distance,
        )

        shortest_distance = pass_and_relaxation(
            graph_backward,
            v_bwd,
            visited_backward,
            visited_forward,
            cst_bwd,
            cst_fwd,
            queue_backward,
            parent_backward,
            shortest_distance,
        )

        if cst_fwd[v_fwd] + cst_bwd[v_bwd] >= shortest_distance:
            break

    if shortest_distance != np.inf:
        shortest_path_distance = shortest_distance
    return shortest_path_distance
