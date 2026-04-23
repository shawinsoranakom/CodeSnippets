def apply_tweaks(node: dict[str, Any], node_tweaks: dict[str, Any]) -> None:
    template_data = node.get("data", {}).get("node", {}).get("template")

    if not isinstance(template_data, dict):
        logger.warning(f"Template data for node {node.get('id')} should be a dictionary")
        return

    for tweak_name, tweak_value in node_tweaks.items():
        if tweak_name not in template_data:
            continue
        if tweak_name == "code":
            logger.warning("Security: Code field cannot be overridden via tweaks.")
            continue
        if tweak_name in template_data:
            field_type = template_data[tweak_name].get("type", "")
            if field_type == "NestedDict":
                value = validate_and_repair_json(tweak_value)
                template_data[tweak_name]["value"] = value
            elif field_type == "mcp":
                # MCP fields expect dict values to be set directly
                template_data[tweak_name]["value"] = tweak_value
            elif field_type == "dict" and isinstance(tweak_value, dict):
                # Dict fields: set the dict directly as the value.
                # If the tweak is wrapped in {"value": <actual>}, unwrap it
                # to support the template-format style (e.g. from UI exports).
                # Caveat: a legitimate single-key dict {"value": x} will be unwrapped.
                if len(tweak_value) == 1 and "value" in tweak_value:
                    template_data[tweak_name]["value"] = tweak_value["value"]
                else:
                    template_data[tweak_name]["value"] = tweak_value
            elif isinstance(tweak_value, dict):
                for k, v in tweak_value.items():
                    k_ = "file_path" if field_type == "file" else k
                    template_data[tweak_name][k_] = v
                # If the user didn't explicitly set load_from_db in the dict,
                # we default to False for the override.
                if "load_from_db" not in tweak_value and "load_from_db" in template_data[tweak_name]:
                    template_data[tweak_name]["load_from_db"] = False
            else:
                key = "file_path" if field_type == "file" else "value"
                template_data[tweak_name][key] = tweak_value
                if "load_from_db" in template_data[tweak_name]:
                    template_data[tweak_name]["load_from_db"] = False