def ordering(signatures: Iterable[tuple[type, ...]]) -> list[tuple[type, ...]]:
    """A sane ordering of signatures to check, first to last
    Topological sort of edges as given by ``edge`` and ``supercedes``
    """
    signatures = list(map(tuple, signatures))
    edges = [(a, b) for a in signatures for b in signatures if edge(a, b)]
    edges = groupby(operator.itemgetter(0), edges)
    for s in signatures:
        if s not in edges:
            edges[s] = []
    topo_edges: dict[
        tuple[type, ...], list[tuple[type, ...]]
    ] = {  # pyrefly: ignore[bad-assignment]
        k: [b for a, b in v]
        for k, v in edges.items()  # type: ignore[attr-defined]
    }
    return _toposort(topo_edges)