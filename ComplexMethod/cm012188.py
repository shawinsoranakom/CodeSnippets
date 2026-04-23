def _find_connected_components(span: list[fx.Node]) -> list[list[fx.Node]]:
    """Find connected components within a span of fusible nodes.

    Two nodes are connected if one is an input to the other (direct data dependency).
    """
    if not span:
        return []

    from torch.fx.experimental.optimization import UnionFind

    span_set = OrderedSet(span)
    node_to_idx = {n: i for i, n in enumerate(span)}

    uf = UnionFind(len(span))
    for i in range(len(span)):
        uf.make_set(i)

    # Union nodes based on input edges
    for node in span:
        node_idx = node_to_idx[node]
        for inp in node.all_input_nodes:
            if inp in span_set:
                uf.join(node_idx, node_to_idx[inp])

    # Group by root
    root_to_nodes: dict[int, list[fx.Node]] = {}
    for node in span:
        root = uf.find(node_to_idx[node])
        if root not in root_to_nodes:
            root_to_nodes[root] = []
        root_to_nodes[root].append(node)

    return list(root_to_nodes.values())