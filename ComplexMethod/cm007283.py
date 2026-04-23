def _get_invalid_components(
    nodes: list[dict],
    type_to_current_hash: dict[str, set[str]],
) -> tuple[list[str], list[str]]:
    """Walk nodes and classify invalid components."""
    blocked: list[str] = []
    outdated: list[str] = []

    for node in nodes:
        node_data = node.get("data", {})
        node_info = node_data.get("node", {})

        component_type = node_data.get("type")
        if not component_type:
            continue

        node_template = node_info.get("template", {})
        node_code_field = node_template.get("code", {})
        node_code = node_code_field.get("value") if isinstance(node_code_field, dict) else None

        if not node_code:
            continue

        display_name = node_info.get("display_name") or component_type
        node_id = node_data.get("id") or node.get("id", "unknown")
        label = f"{display_name} ({node_id})"

        expected_hashes = type_to_current_hash.get(component_type)
        if expected_hashes is None:
            blocked.append(label)
        else:
            node_hash = _compute_code_hash(node_code)
            if node_hash not in expected_hashes:
                outdated.append(label)

        flow_data = node_info.get("flow", {})
        if isinstance(flow_data, dict):
            nested_data = flow_data.get("data", {})
            nested_nodes = nested_data.get("nodes", [])
            if nested_nodes:
                nested_blocked, nested_outdated = _get_invalid_components(
                    nested_nodes,
                    type_to_current_hash,
                )
                blocked.extend(nested_blocked)
                outdated.extend(nested_outdated)

    return blocked, outdated