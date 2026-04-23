def depth_first_search(graph: dict, vertex: int, visited: set, rec_stk: set) -> bool:
    visited.add(vertex)
    rec_stk.add(vertex)

    for node in graph[vertex]:
        if node not in visited:
            if depth_first_search(graph, node, visited, rec_stk):
                return True
        elif node in rec_stk:
            return True

    rec_stk.remove(vertex)
    return False
