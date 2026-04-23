def _resolve_input_types(flow: dict, component_id: str, input_name: str) -> tuple[list[str], str]:
    """Look up input types and field type from the component's template.

    Raises ValueError if the component or input is not found.
    """
    for node in flow.get("data", {}).get("nodes", []):
        node_data = node.get("data", {})
        nid = node_data.get("id", node.get("id", ""))
        if nid != component_id:
            continue
        template = node_data.get("node", {}).get("template", {})
        field = template.get(input_name, {})
        if isinstance(field, dict) and field:
            return field.get("input_types", ["Message"]), field.get("type", "str")
        available = [k for k, v in template.items() if isinstance(v, dict) and v.get("input_types")]
        msg = f"Input '{input_name}' not found on component '{component_id}'. Available: {available}"
        raise ValueError(msg)
    msg = f"Component not found in flow: {component_id}"
    raise ValueError(msg)