def edglist():
    n, m = tuple(map(int, input().split(" ")))
    edges = []
    for _ in range(m):
        edges.append(tuple(map(int, input().split(" "))))
    return edges, n
