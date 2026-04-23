def _check_structural(flow: dict[str, Any], result: ValidationResult) -> bool:
    """Return False if the flow is so broken that further checks cannot run."""
    ok = True
    missing_top = _REQUIRED_TOP_LEVEL - set(flow.keys())
    for key in sorted(missing_top):
        result.issues.append(
            _make_issue(
                level=_LEVEL_STRUCTURAL,
                severity="error",
                node_id=None,
                node_name=None,
                message=f"Missing required top-level field: '{key}'",
            )
        )
        ok = False

    data = flow.get("data")
    if not isinstance(data, dict):
        result.issues.append(
            _make_issue(
                level=_LEVEL_STRUCTURAL,
                severity="error",
                node_id=None,
                node_name=None,
                message="'data' must be a JSON object",
            )
        )
        return False

    missing_data = _REQUIRED_DATA_KEYS - set(data.keys())
    for key in sorted(missing_data):
        result.issues.append(
            _make_issue(
                level=_LEVEL_STRUCTURAL,
                severity="error",
                node_id=None,
                node_name=None,
                message=f"Missing required field: 'data.{key}'",
            )
        )
        ok = False

    nodes = data.get("nodes", [])
    if not isinstance(nodes, list):
        result.issues.append(
            _make_issue(
                level=_LEVEL_STRUCTURAL,
                severity="error",
                node_id=None,
                node_name=None,
                message="'data.nodes' must be a JSON array",
            )
        )
        return False

    for i, node in enumerate(nodes):
        if not isinstance(node, dict):
            result.issues.append(
                _make_issue(
                    level=_LEVEL_STRUCTURAL,
                    severity="error",
                    node_id=None,
                    node_name=None,
                    message=f"Node at index {i} is not a JSON object",
                )
            )
            ok = False
            continue
        for req in ("id", "data"):
            if req not in node:
                result.issues.append(
                    _make_issue(
                        level=_LEVEL_STRUCTURAL,
                        severity="error",
                        node_id=node.get("id"),
                        node_name=_node_display_name(node),
                        message=f"Node at index {i} is missing required field '{req}'",
                    )
                )
                ok = False

        node_data = node.get("data", {})
        if isinstance(node_data, dict) and "type" not in node_data:
            result.issues.append(
                _make_issue(
                    level=_LEVEL_STRUCTURAL,
                    severity="warning",
                    node_id=node.get("id"),
                    node_name=_node_display_name(node),
                    message="Node is missing 'data.type' -- component type cannot be determined",
                )
            )

    return ok