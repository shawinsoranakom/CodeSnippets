def _check_edge_type_compatibility(flow: dict[str, Any], result: ValidationResult) -> None:
    """Check that source output types are compatible with target input types.

    This is a best-effort check: if type information is missing from the node
    template we emit a warning rather than an error.
    """
    data = flow.get("data", {})
    nodes_by_id: dict[str, dict[str, Any]] = {
        n["id"]: n for n in data.get("nodes", []) if isinstance(n, dict) and "id" in n
    }

    for edge in data.get("edges", []):
        if not isinstance(edge, dict):
            continue
        src_id: str | None = edge.get("source")
        tgt_id: str | None = edge.get("target")
        src_handle: dict[str, Any] = edge.get("data", {}).get("sourceHandle", {}) or {}
        tgt_handle: dict[str, Any] = edge.get("data", {}).get("targetHandle", {}) or {}

        if not src_id or not tgt_id:
            continue

        src_node = nodes_by_id.get(src_id)
        tgt_node = nodes_by_id.get(tgt_id)
        if not src_node or not tgt_node:
            result.issues.append(
                _make_issue(
                    level=_LEVEL_EDGE_TYPES,
                    severity="error",
                    node_id=None,
                    node_name=None,
                    message=(f"Edge references non-existent node(s): source={src_id!r}, target={tgt_id!r}"),
                )
            )
            continue

        output_types: list[str] = src_handle.get("output_types", [])
        src_type: str | None = output_types[0] if output_types else None
        tgt_type: str | None = tgt_handle.get("type")

        if src_type and tgt_type and tgt_type not in {src_type, "Any"}:
            result.issues.append(
                _make_issue(
                    level=_LEVEL_EDGE_TYPES,
                    severity="warning",
                    node_id=tgt_id,
                    node_name=_node_display_name(tgt_node),
                    message=(
                        f"Possible type mismatch on edge from "
                        f"'{_node_display_name(src_node)}' -> '{_node_display_name(tgt_node)}': "
                        f"source emits '{src_type}', target expects '{tgt_type}'"
                    ),
                )
            )