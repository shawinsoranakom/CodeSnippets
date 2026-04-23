async def _create_prompt_template_vars(flow_id: str, parsed: dict, id_map: dict[str, str]) -> None:
    """Create dynamic input fields for Prompt template variables.

    When a Prompt Template's template contains {variable_name} placeholders,
    the UI creates input fields for them. This function does the same so that
    edges can connect to those fields.
    """
    # Find Prompt nodes that have template config
    node_types = {n["id"]: n["type"] for n in parsed["nodes"]}
    prompt_nodes = {sid for sid, ntype in node_types.items() if ntype in PROMPT_TYPES}
    if not prompt_nodes:
        return

    flow = await _get_flow(flow_id)
    changed = False

    for spec_id in prompt_nodes:
        real_id = id_map.get(spec_id)
        if real_id is None:
            continue

        # Find the node in the flow
        node = None
        for n in flow.get("data", {}).get("nodes", []):
            if n.get("data", {}).get("id") == real_id:
                node = n
                break
        if node is None:
            continue

        template = node["data"].get("node", {}).get("template", {})
        template_value = ""
        if isinstance(template.get("template"), dict):
            template_value = template["template"].get("value", "")

        if not template_value:
            continue

        # Parse {variable_name} placeholders
        variables = _TEMPLATE_VAR_RE.findall(template_value)
        for var_name in variables:
            if var_name in template:
                continue  # already exists
            template[var_name] = {
                "_input_type": "MessageInput",
                "advanced": False,
                "display_name": var_name,
                "dynamic": False,
                "info": "",
                "input_types": ["Message"],
                "list": False,
                "load_from_db": False,
                "name": var_name,
                "placeholder": "",
                "required": False,
                "show": True,
                "title_case": False,
                "tool_mode": False,
                "trace_as_metadata": True,
                "type": "str",
                "value": "",
            }
            changed = True

        # Update custom_fields to track template variables
        custom_fields = node["data"]["node"].setdefault("custom_fields", {})
        custom_fields["template"] = variables

    if changed:
        await _patch_flow(flow_id, flow)