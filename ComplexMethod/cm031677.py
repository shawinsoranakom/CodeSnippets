def find_cycles_in_scc(
    graph: dict[str, Set[str]], scc: Set[str], start: str
) -> Iterable[list[str]]:
    """Find cycles in SCC emanating from start.

    Yields lists of the form ['A', 'B', 'C', 'A'], which means there's
    a path from A -> B -> C -> A.  The first item is always the start
    argument, but the last item may be another element, e.g.  ['A',
    'B', 'C', 'B'] means there's a path from A to B and there's a
    cycle from B to C and back.
    """
    # Basic input checks.
    assert start in scc, (start, scc)
    assert scc <= graph.keys(), scc - graph.keys()

    # Reduce the graph to nodes in the SCC.
    graph = {src: {dst for dst in dsts if dst in scc} for src, dsts in graph.items() if src in scc}
    assert start in graph

    # Recursive helper that yields cycles.
    def dfs(node: str, path: list[str]) -> Iterator[list[str]]:
        if node in path:
            yield path + [node]
            return
        path = path + [node]  # TODO: Make this not quadratic.
        for child in graph[node]:
            yield from dfs(child, path)

    yield from dfs(start, [])