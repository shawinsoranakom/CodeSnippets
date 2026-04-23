def _extract_tool_use_result(result: object) -> str:
    """Extract a string from a UserMessage's ``tool_use_result`` dict.

    SDK built-in tools may store their result in ``tool_use_result``
    instead of (or in addition to) ``ToolResultBlock`` content blocks.
    """
    if isinstance(result, str):
        return result
    if isinstance(result, dict):
        # Try common result keys
        for key in ("content", "text", "output", "stdout", "result"):
            val = result.get(key)
            if isinstance(val, str) and val:
                return val
        # Fall back to JSON serialization of the whole dict
        try:
            return json.dumps(result)
        except (TypeError, ValueError):
            return str(result)
    if result is None:
        return ""
    try:
        return json.dumps(result)
    except (TypeError, ValueError):
        return str(result)