def _get_tool_requests(entry: dict[str, Any]) -> list[str]:
    """
    Return a list of tool_call_ids if the entry is a tool request.
    Supports OpenAI Chat Completions, Responses API, and Anthropic formats.
    """
    tool_call_ids = []

    # OpenAI Responses API: function_call items have type="function_call"
    if entry.get("type") == "function_call":
        if call_id := entry.get("call_id"):
            tool_call_ids.append(call_id)
        return tool_call_ids

    if entry.get("role") != "assistant":
        return tool_call_ids

    # OpenAI Chat Completions: check for tool_calls in the entry.
    calls = entry.get("tool_calls")
    if isinstance(calls, list):
        for call in calls:
            if tool_id := call.get("id"):
                tool_call_ids.append(tool_id)

    # Anthropic: check content items for tool_use type.
    content = entry.get("content")
    if isinstance(content, list):
        for item in content:
            if item.get("type") != "tool_use":
                continue
            if tool_id := item.get("id"):
                tool_call_ids.append(tool_id)

    return tool_call_ids