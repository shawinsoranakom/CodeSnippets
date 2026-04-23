def pass_and_relaxation(
    graph: dict,
    v: str,
    visited_forward: set,
    visited_backward: set,
    cst_fwd: dict,
    cst_bwd: dict,
    queue: PriorityQueue,
    parent: dict,
    shortest_distance: float,
) -> float:
    for nxt, d in graph[v]:
        if nxt in visited_forward:
            continue
        old_cost_f = cst_fwd.get(nxt, np.inf)
        new_cost_f = cst_fwd[v] + d
        if new_cost_f < old_cost_f:
            queue.put((new_cost_f, nxt))
            cst_fwd[nxt] = new_cost_f
            parent[nxt] = v
        if (
            nxt in visited_backward
            and cst_fwd[v] + d + cst_bwd[nxt] < shortest_distance
        ):
            shortest_distance = cst_fwd[v] + d + cst_bwd[nxt]
    return shortest_distance
