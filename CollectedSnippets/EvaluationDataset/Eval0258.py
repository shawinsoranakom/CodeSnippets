def lowest_common_ancestor(
    u: int, v: int, level: list[int], parent: list[list[int]]
) -> int:
    if level[u] < level[v]:
        u, v = swap(u, v)
    for i in range(18, -1, -1):
        if level[u] - (1 << i) >= level[v]:
            u = parent[i][u]
    if u == v:
        return u
    for i in range(18, -1, -1):
        if parent[i][u] not in [0, parent[i][v]]:
            u, v = parent[i][u], parent[i][v]
    return parent[0][u]

