def parse_mcp_content(content: list[dict[str, Any]]) -> Any:
    """Parse MCP tool response content into a plain Python value.

    - text items: parsed as JSON when possible, kept as str otherwise
    - image items: kept as ``{type, data, mimeType}`` dict for frontend rendering
    - resource items: unwrapped to their resource payload dict

    Single-item responses are unwrapped from the list; multiple items are
    returned as a list; empty content returns ``None``.
    """
    output_parts: list[Any] = []
    for item in content:
        item_type = item.get("type")
        if item_type == "text":
            text = item.get("text", "")
            try:
                output_parts.append(json.loads(text))
            except (json.JSONDecodeError, ValueError):
                output_parts.append(text)
        elif item_type == "image":
            output_parts.append(
                {
                    "type": "image",
                    "data": item.get("data"),
                    "mimeType": item.get("mimeType"),
                }
            )
        elif item_type == "resource":
            output_parts.append(item.get("resource", {}))

    if len(output_parts) == 1:
        return output_parts[0]
    return output_parts or None