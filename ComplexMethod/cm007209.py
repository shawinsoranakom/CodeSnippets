def layout_flow(flow: dict) -> None:
    """Assign positions to all nodes in a flow based on edge topology."""
    nodes = flow.get("data", {}).get("nodes", [])
    edges = flow.get("data", {}).get("edges", [])

    if not nodes:
        return

    node_ids = [_node_id(n) for n in nodes]
    id_to_node = {_node_id(n): n for n in nodes}

    # Build adjacency: source -> [targets]
    successors: dict[str, list[str]] = defaultdict(list)
    predecessors: dict[str, list[str]] = defaultdict(list)
    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src in id_to_node and tgt in id_to_node:
            successors[src].append(tgt)
            predecessors[tgt].append(src)

    # Assign layers via longest path from sources (nodes with no predecessors)
    layers = _assign_layers(node_ids, successors, predecessors)

    # Group nodes by layer
    layer_groups: dict[int, list[str]] = defaultdict(list)
    for nid, layer in layers.items():
        layer_groups[layer].append(nid)

    # Assign positions
    for layer_idx, group in sorted(layer_groups.items()):
        x = layer_idx * LAYER_SPACING_X
        total_height = (len(group) - 1) * NODE_SPACING_Y
        start_y = -total_height / 2
        for i, nid in enumerate(group):
            node = id_to_node[nid]
            node["position"] = {"x": x, "y": start_y + i * NODE_SPACING_Y}