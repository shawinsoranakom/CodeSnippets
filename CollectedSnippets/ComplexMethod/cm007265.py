async def configure_component(
    flow_id: str,
    component_id: str,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Set parameter values on a component.

    Use get_component_info to check current values, or describe_component_type
    to see available fields. Some fields trigger server-side template updates
    (e.g. changing model_name may update available options) -- the response
    reflects the final state, no need to re-fetch.

    Args:
        flow_id: The flow UUID.
        component_id: The component ID.
        params: Dict of parameter names to values (e.g. {"model_name": "gpt-4o", "temperature": 0.5}).
    """
    client = _get_client()
    flow = await _get_flow(flow_id)

    # Find the node to check for dynamic fields
    node = None
    for n in flow.get("data", {}).get("nodes", []):
        nid = n.get("data", {}).get("id", n.get("id", ""))
        if nid == component_id:
            node = n
            break

    if node is None:
        msg = f"Component not found: {component_id}"
        raise ValueError(msg)

    template = node["data"].get("node", {}).get("template", {})

    # Separate dynamic fields from static ones
    static_params = {}
    warnings = []
    for key, value in params.items():
        if needs_server_update(template, key):
            # Handle tool_mode specially
            if key == "tool_mode":
                enabled = value in (True, "true", "True", "1", 1)
                code = template.get("code", {}).get("value", "")
                updated = await client.post(
                    "/custom_component/update",
                    json_data={
                        "code": code,
                        "template": template,
                        "field": "tool_mode",
                        "field_value": enabled,
                        "tool_mode": enabled,
                    },
                )
                if not isinstance(updated, dict) or "template" not in updated:
                    msg = f"Server returned invalid response for tool_mode update on '{component_id}'"
                    raise RuntimeError(msg)
                node["data"]["node"] = updated
                template = updated["template"]
            else:
                # Set value in template before sending
                if key in template and isinstance(template[key], dict):
                    template[key]["value"] = value
                else:
                    template[key] = {"value": value}
                code = template.get("code", {}).get("value", "")
                tool_mode = node["data"]["node"].get("tool_mode", False)
                try:
                    updated = await client.post(
                        "/custom_component/update",
                        json_data={
                            "code": code,
                            "template": template,
                            "field": key,
                            "field_value": value,
                            "tool_mode": tool_mode,
                        },
                    )
                except RuntimeError:
                    # Server refresh failed (e.g. missing API key for model list).
                    # The value is already set in the template above, so save it
                    # locally and warn the agent.
                    warnings.append(
                        f"Field '{key}' was set to '{value}' but the server-side "
                        f"refresh failed. This usually means a required credential "
                        f"(like an API key) is not configured on the component yet. "
                        f"Set the credential first, then reconfigure '{key}'."
                    )
                    continue
                if not isinstance(updated, dict) or "template" not in updated:
                    msg = f"Server returned invalid response for '{key}' update on '{component_id}'"
                    raise RuntimeError(msg)
                node["data"]["node"] = updated
                template = updated["template"]
        else:
            static_params[key] = value

    # Apply static params
    if static_params:
        fb_configure(flow, component_id, static_params)

    await _patch_flow(flow_id, flow)
    await _get_client().post_event(flow_id, "component_configured", f"Configured {component_id}")
    result: dict[str, Any] = {"component_id": component_id, "configured": list(params.keys())}
    if warnings:
        result["warnings"] = warnings
    return result