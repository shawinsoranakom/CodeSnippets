def _toposort(edges: dict[_T, Iterable[_T]]) -> list[_T]:
    """Topological sort algorithm by Kahn [1] - O(nodes + vertices)
    inputs:
        edges - a dict of the form {a: {b, c}} where b and c depend on a
    outputs:
        L - an ordered list of nodes that satisfy the dependencies of edges
    >>> # xdoctest: +SKIP
    >>> _toposort({1: (2, 3), 2: (3,)})
    [1, 2, 3]
    Closely follows the wikipedia page [2]
    [1] Kahn, Arthur B. (1962), "Topological sorting of large networks",
    Communications of the ACM
    [2] http://en.wikipedia.org/wiki/Toposort#Algorithms
    """
    incoming_edges = reverse_dict(edges)
    incoming_edges = {k: set(val) for k, val in incoming_edges.items()}
    S = {v for v in edges if v not in incoming_edges}
    L = []

    while S:
        n = S.pop()
        L.append(n)
        for m in edges.get(n, ()):
            if n not in incoming_edges[m]:
                raise AssertionError(f"Expected {n} in incoming_edges[{m}]")
            incoming_edges[m].remove(n)
            if not incoming_edges[m]:
                S.add(m)
    if any(incoming_edges.get(v) for v in edges):
        raise ValueError("Input has cycles")
    return L