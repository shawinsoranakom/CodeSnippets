def create_sparse(max_node: int, parent: list[list[int]]) -> list[list[int]]:
    j = 1
    while (1 << j) < max_node:
        for i in range(1, max_node + 1):
            parent[j][i] = parent[j - 1][parent[j - 1][i]]
        j += 1
    return parent

