def _check_required_inputs(flow: dict[str, Any], result: ValidationResult) -> None:
    """Verify that all required input fields have a value or an incoming edge."""
    data = flow.get("data", {})
    nodes = data.get("nodes", [])
    edges = data.get("edges", [])

    # Build set of (node_id, field_name) pairs that receive an edge
    connected_inputs: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        tgt_id = edge.get("target")
        tgt_handle = edge.get("data", {}).get("targetHandle", {}) or {}
        field_name = tgt_handle.get("fieldName")
        if tgt_id and field_name:
            connected_inputs.add((tgt_id, field_name))

    for node in nodes:
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        node_data = node.get("data", {})
        template: dict[str, Any] = node_data.get("node", {}).get("template", {})

        for field_name, field_def in template.items():
            if field_name.startswith("_") or not isinstance(field_def, dict):
                continue
            is_required = field_def.get("required", False)
            show = field_def.get("show", True)
            if not is_required or not show:
                continue

            has_value = field_def.get("value") not in (None, "", [], {})
            has_edge = (node_id, field_name) in connected_inputs

            if not has_value and not has_edge:
                result.issues.append(
                    _make_issue(
                        level=_LEVEL_REQUIRED_INPUTS,
                        severity="error",
                        node_id=node_id,
                        node_name=_node_display_name(node),
                        message=f"Required input '{field_name}' has no value and no incoming edge",
                    )
                )