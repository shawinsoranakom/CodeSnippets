def ordering(signatures: Iterable[object]) -> list[object]:
    """A sane ordering of signatures to check, first to last
    Topological sort of edges as given by ``edge`` and ``supercedes``
    """
    signatures = list(map(tuple, signatures))  # pyrefly: ignore[bad-argument-type]
    edges = [(a, b) for a in signatures for b in signatures if edge(a, b)]
    edges = groupby(first, edges)
    for s in signatures:
        if s not in edges:
            edges[s] = []
    edges = {k: [b for a, b in v] for k, v in edges.items()}  # type: ignore[attr-defined, assignment]
    return _toposort(edges)