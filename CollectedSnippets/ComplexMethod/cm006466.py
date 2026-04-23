def _collect_candidate_variable_keys_from_flow_data(data: dict) -> set[str]:
    """Collect explicit global-variable keys from flow data."""
    candidate_keys: set[str] = set()

    for node in data.get("nodes", []):
        template = node.get("data", {}).get("node", {}).get("template", {})
        if not isinstance(template, dict):
            continue
        for field in template.values():
            if not isinstance(field, dict):
                continue
            if field.get("load_from_db") is True:
                var_name = field.get("value")
                normalized_var_name = var_name.strip() if isinstance(var_name, str) else None
                if normalized_var_name:
                    candidate_keys.add(normalized_var_name)

    return candidate_keys