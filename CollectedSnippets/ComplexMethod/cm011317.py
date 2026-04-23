def reverse_closure(
    roots: list[Node], target_nodes: set[Node], reverse_edges_dict
) -> tuple[set[Node], set[Node]]:
    """
    This function returns the reverse closure of the given roots,
    i.e. the set of nodes that can be reached from the roots by following the
    reverse edges of the graph. The target_nodes are the nodes that we want to
    include in the closure.
    """
    # Recurse until we reach a target node
    closure: set[Node] = set()
    visited_target_nodes = set()
    q: collections.deque[Node] = collections.deque()
    for node in roots:
        if node is not None and node not in closure:
            closure.add(node)
            q.append(node)
    while q:
        node = q.popleft()
        reverse_edges = reverse_edges_dict[node]
        for fn in reverse_edges:
            if fn in closure or fn is None:
                continue
            if fn in target_nodes:
                visited_target_nodes.add(fn)
                continue
            closure.add(fn)
            q.append(fn)
    return closure, visited_target_nodes