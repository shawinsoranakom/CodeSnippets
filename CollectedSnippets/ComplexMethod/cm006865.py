def _check_unused_nodes(flow: dict[str, Any], result: ValidationResult) -> None:
    """Warn about nodes whose outputs never reach an output node.

    Walks the graph backwards from every node whose ``data.type`` ends with
    ``"Output"`` (e.g. ``ChatOutput``, ``TextOutput``).  Any node that is not
    reachable from an output node is considered unused.

    Single-node flows and flows with no output nodes are skipped.
    """
    data = flow.get("data", {})
    nodes: list[dict[str, Any]] = [n for n in data.get("nodes", []) if isinstance(n, dict) and "id" in n]
    edges: list[dict[str, Any]] = [e for e in data.get("edges", []) if isinstance(e, dict)]

    if len(nodes) <= 1:
        return

    # Build reverse adjacency: for each node, which nodes feed INTO it
    # (i.e. target -> {sources})
    predecessors: dict[str, set[str]] = {n["id"]: set() for n in nodes}
    for edge in edges:
        src = edge.get("source")
        tgt = edge.get("target")
        if src and tgt and tgt in predecessors:
            predecessors[tgt].add(src)

    # Identify output nodes by type suffix
    output_node_ids: set[str] = set()
    for node in nodes:
        component_type: str = node.get("data", {}).get("type", "") or ""
        if component_type.endswith("Output"):
            output_node_ids.add(node["id"])

    if not output_node_ids:
        return  # can't determine "useful" without knowing output nodes

    # BFS backwards from all output nodes to find every contributing node
    reachable: set[str] = set()
    queue: list[str] = list(output_node_ids)
    while queue:
        current = queue.pop()
        if current in reachable:
            continue
        reachable.add(current)
        queue.extend(predecessors.get(current, set()) - reachable)

    nodes_by_id = {n["id"]: n for n in nodes}
    for node_id, node in nodes_by_id.items():
        if node_id not in reachable:
            result.issues.append(
                _make_issue(
                    level=_LEVEL_STRUCTURAL,
                    severity="warning",
                    node_id=node_id,
                    node_name=_node_display_name(node),
                    message="Unused node: does not contribute to any output",
                )
            )