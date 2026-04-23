def _check_missing_credentials(flow: dict[str, Any], result: ValidationResult) -> None:
    """Warn when password/secret fields have no value and no matching env var.

    A template field is considered a *credential field* when it has
    ``"password": true`` (or ``"display_password": true``).  If no value is
    stored in the flow JSON *and* no corresponding environment variable is set
    *and* the field has no incoming edge, a warning is emitted so the user
    knows to provide the secret before running the flow.

    The environment variable name is derived by uppercasing the field name and
    replacing hyphens with underscores (e.g. ``openai_api_key`` ->
    ``OPENAI_API_KEY``).
    """
    data = flow.get("data", {})
    edges = data.get("edges", [])

    # Build the set of (node_id, field_name) pairs that receive an edge
    connected_inputs: set[tuple[str, str]] = set()
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        tgt_id = edge.get("target")
        tgt_handle = edge.get("data", {}).get("targetHandle", {}) or {}
        field_name = tgt_handle.get("fieldName")
        if tgt_id and field_name:
            connected_inputs.add((tgt_id, field_name))

    for node in data.get("nodes", []):
        if not isinstance(node, dict):
            continue
        node_id = node.get("id")
        node_data = node.get("data", {})
        template: dict[str, Any] = node_data.get("node", {}).get("template", {})

        for field_name, field_def in template.items():
            if field_name.startswith("_") or not isinstance(field_def, dict):
                continue

            is_credential = field_def.get("password", False) or field_def.get("display_password", False)
            if not is_credential:
                continue

            show = field_def.get("show", True)
            if not show:
                continue

            # Already satisfied? Check value, incoming edge, or env var.
            has_value = bool(field_def.get("value"))
            has_edge = (node_id, field_name) in connected_inputs
            if has_value or has_edge:
                continue

            env_key = field_name.upper().replace("-", "_")
            if os.environ.get(env_key):
                continue

            result.issues.append(
                _make_issue(
                    level=_LEVEL_REQUIRED_INPUTS,
                    severity="warning",
                    node_id=node_id,
                    node_name=_node_display_name(node),
                    message=(
                        f"Credential field '{field_name}' has no value "
                        f"(set ${env_key} or configure via global variables)"
                    ),
                )
            )