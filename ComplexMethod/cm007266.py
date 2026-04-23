async def get_component_info(
    flow_id: str,
    component_id: str,
    field_name: str | None = None,
) -> dict[str, Any]:
    """Get a specific component instance's current parameter values and outputs.

    Unlike describe_component_type (which shows the type definition),
    this returns the actual values set on a component in a flow.
    Sensitive fields (API keys, passwords) are redacted.

    Args:
        flow_id: The flow UUID.
        component_id: The component ID.
        field_name: Optional -- narrow the response to a single field.
    """
    flow = await _get_flow(flow_id)
    info = fb_get_component(flow, component_id)

    # Redact sensitive params (checks field name against SENSITIVE_KEYWORDS)
    from lfx.mcp.redact import is_sensitive_field

    for key in list(info.get("params", {}).keys()):
        if is_sensitive_field(key) and info["params"][key]:
            info["params"][key] = "***REDACTED***"

    if field_name is None:
        return info

    # Return just the requested field
    if field_name not in info.get("params", {}):
        available = list(info.get("params", {}).keys())
        msg = f"Field '{field_name}' not found on component '{component_id}'. Available: {available}"
        raise ValueError(msg)

    # Get the raw field metadata from the node template
    node = None
    for n in flow.get("data", {}).get("nodes", []):
        nid = n.get("data", {}).get("id", n.get("id", ""))
        if nid == component_id:
            node = n
            break

    field_meta = {}
    if node is not None:
        template = node["data"].get("node", {}).get("template", {})
        raw_field = template.get(field_name, {})
        if isinstance(raw_field, dict):
            field_meta = {
                "type": raw_field.get("type", ""),
                "display_name": raw_field.get("display_name", field_name),
                "required": raw_field.get("required", False),
                "real_time_refresh": raw_field.get("real_time_refresh", False),
            }

    return {
        "component_id": component_id,
        "field_name": field_name,
        "value": info["params"][field_name],
        **field_meta,
    }