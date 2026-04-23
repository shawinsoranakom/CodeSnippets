def _assign_layers(
    node_ids: list[str],
    successors: dict[str, list[str]],
    predecessors: dict[str, list[str]],
) -> dict[str, int]:
    """Assign each node to a layer using longest-path layering."""
    layers: dict[str, int] = {}
    in_degree = {nid: len(predecessors.get(nid, [])) for nid in node_ids}

    # Start with source nodes (no predecessors)
    queue = deque()
    for nid in node_ids:
        if in_degree[nid] == 0:
            queue.append(nid)
            layers[nid] = 0

    # BFS: each node's layer = max(predecessor layers) + 1
    while queue:
        nid = queue.popleft()
        for succ in successors.get(nid, []):
            new_layer = layers[nid] + 1
            if succ not in layers or new_layer > layers[succ]:
                layers[succ] = new_layer
            in_degree[succ] -= 1
            if in_degree[succ] == 0:
                queue.append(succ)

    # Handle disconnected nodes (no edges)
    next_layer = max(layers.values(), default=-1) + 1
    for nid in node_ids:
        if nid not in layers:
            layers[nid] = next_layer
            next_layer += 1

    return layers