def check_cycle(graph: dict) -> bool:
    visited: set[int] = set()
    rec_stk: set[int] = set()
    return any(
        node not in visited and depth_first_search(graph, node, visited, rec_stk)
        for node in graph
    )
