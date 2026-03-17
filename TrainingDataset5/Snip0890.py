def dfs(graph: dict, vert: int, visited: list) -> list:
    visited[vert] = True
    connected_verts = []

    for neighbour in graph[vert]:
        if not visited[neighbour]:
            connected_verts += dfs(graph, neighbour, visited)

    return [vert, *connected_verts]
