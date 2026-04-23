def _check_orphaned_nodes(flow: dict[str, Any], result: ValidationResult) -> None:
    """Warn about nodes that have no edges connecting them to the rest of the graph.

    A node is *orphaned* when it appears in no edge (neither as source nor as
    target).  Single-node flows are exempt.
    """
    data = flow.get("data", {})
    nodes: list[dict[str, Any]] = [n for n in data.get("nodes", []) if isinstance(n, dict) and "id" in n]
    edges: list[dict[str, Any]] = [e for e in data.get("edges", []) if isinstance(e, dict)]

    if len(nodes) <= 1:
        return  # single-node flows are always "connected"

    connected_ids: set[str] = set()
    for edge in edges:
        if edge.get("source"):
            connected_ids.add(edge["source"])
        if edge.get("target"):
            connected_ids.add(edge["target"])

    for node in nodes:
        node_id = node["id"]
        if node_id not in connected_ids:
            result.issues.append(
                _make_issue(
                    level=_LEVEL_STRUCTURAL,
                    severity="warning",
                    node_id=node_id,
                    node_name=_node_display_name(node),
                    message="Orphaned node: not connected to any other node",
                )
            )