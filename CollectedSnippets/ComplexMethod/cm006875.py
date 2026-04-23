def update_frontend_node_with_template_values(frontend_node, raw_frontend_node):
    """Updates the given frontend node with values from the raw template data.

    :param frontend_node: A dict representing a built frontend node.
    :param raw_frontend_node: A dict representing raw template data.
    :return: Updated frontend node.
    """
    if not is_valid_data(frontend_node, raw_frontend_node):
        return frontend_node

    update_template_values(frontend_node["template"], raw_frontend_node["template"])

    old_code = raw_frontend_node["template"]["code"]["value"]
    new_code = frontend_node["template"]["code"]["value"]
    frontend_node["edited"] = raw_frontend_node.get("edited", False) or (old_code != new_code)

    # Compute tool modes from template
    tool_modes = [
        value.get("tool_mode")
        for key, value in frontend_node["template"].items()
        if key != "_type" and isinstance(value, dict)
    ]

    if any(tool_modes):
        frontend_node["tool_mode"] = raw_frontend_node.get("tool_mode", False)
    else:
        frontend_node["tool_mode"] = False

    if not frontend_node.get("edited", False):
        frontend_node["display_name"] = raw_frontend_node.get("display_name", frontend_node.get("display_name", ""))
        frontend_node["description"] = raw_frontend_node.get("description", frontend_node.get("description", ""))

    return frontend_node