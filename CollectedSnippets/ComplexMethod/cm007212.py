def flow_graph_repr(flow: dict) -> str:
    """Build an ASCII DAG representation of a flow's graph.

    Uses lfx's ASCII graph renderer (grandalf-based Sugiyama layout),
    falling back to a simple chain representation if unavailable.
    """
    data = flow.get("data", {})
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    if not nodes:
        return "(empty)"

    # Build id -> label map, disambiguating duplicate types
    id_to_label: dict[str, str] = {}
    type_count: dict[str, int] = {}
    for node in nodes:
        nd = node.get("data", {})
        nid = nd.get("id", node.get("id", ""))
        node_type = nd.get("type", "?")
        count = type_count.get(node_type, 0) + 1
        type_count[node_type] = count
        id_to_label[nid] = f"{node_type} #{count}" if count > 1 else node_type

    # Go back and suffix the first occurrence too when there are duplicates
    for nid, label in id_to_label.items():
        if "#" not in label and type_count.get(label, 0) > 1:
            id_to_label[nid] = f"{label} #1"

    if not edges:
        return ", ".join(sorted(id_to_label.values()))

    vertexes = list(id_to_label.values())
    edge_pairs = []
    for edge in edges:
        src_label = id_to_label.get(edge.get("source", ""))
        tgt_label = id_to_label.get(edge.get("target", ""))
        if src_label and tgt_label:
            edge_pairs.append((src_label, tgt_label))

    try:
        from lfx.graph.graph.ascii import draw_graph

        return draw_graph(vertexes, edge_pairs, return_ascii=True) or "(empty)"
    except ImportError:
        # grandalf not available; fall back to simple representation
        return ", ".join(f"{s} -> {t}" for s, t in edge_pairs)