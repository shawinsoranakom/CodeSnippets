def _extract_allowed_tools_from_mcp_requests(
    tools: list[Tool],
) -> dict[str, list[str] | None]:
    """
    Extract allowed_tools mapping from MCP tool requests.

    Returns a dictionary mapping server_label to allowed_tools list.
    Handles both list format and McpAllowedToolsMcpToolFilter object format.

    Special handling:
    - If allowed_tools is None, returns None (allows all tools)
    - If allowed_tools contains "*", returns None (allows all tools)
    - Otherwise, returns the list of specific tool names

    This function can be reused for both harmony and non-harmony MCP calls.
    """
    allowed_tools_map: dict[str, list[str] | None] = {}
    for tool in tools:
        if not isinstance(tool, Mcp):
            continue

        # allowed_tools can be a list or an object with tool_names
        # Extract the actual list of tool names
        allowed_tools_val = None
        if tool.allowed_tools is not None:
            if isinstance(tool.allowed_tools, list):
                allowed_tools_val = tool.allowed_tools
            elif hasattr(tool.allowed_tools, "tool_names"):
                # It's an McpAllowedToolsMcpToolFilter object
                allowed_tools_val = tool.allowed_tools.tool_names

        # Normalize "*" to None (both mean "allow all tools")
        if allowed_tools_val is not None and "*" in allowed_tools_val:
            allowed_tools_val = None

        allowed_tools_map[tool.server_label] = allowed_tools_val
    return allowed_tools_map