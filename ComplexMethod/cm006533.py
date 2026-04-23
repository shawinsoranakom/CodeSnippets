def remove_api_keys(flow: dict):
    """Remove api keys from flow data."""
    for node in flow.get("data", {}).get("nodes", []):
        node_data = node.get("data")
        if not isinstance(node_data, dict):
            continue
        node_inner = node_data.get("node")
        if not isinstance(node_inner, dict):
            continue
        template = node_inner.get("template")
        if not isinstance(template, dict):
            continue
        for value in template.values():
            if isinstance(value, dict) and "name" in value and has_api_terms(value["name"]) and value.get("password"):
                value["value"] = None

    return flow