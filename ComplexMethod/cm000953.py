def _extract_tool_output(content: str | list[dict[str, str]] | None) -> str:
    """Extract a string output from a ToolResultBlock's content field."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = [item.get("text", "") for item in content if item.get("type") == "text"]
        if parts:
            return "".join(parts)
        try:
            return json.dumps(content)
        except (TypeError, ValueError):
            return str(content)
    if content is None:
        return ""
    try:
        return json.dumps(content)
    except (TypeError, ValueError):
        return str(content)