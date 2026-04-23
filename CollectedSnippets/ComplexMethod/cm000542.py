def _get_tool_responses(entry: dict[str, Any]) -> list[str]:
    """
    Return a list of tool_call_ids if the entry is a tool response.
    Supports OpenAI Chat Completions, Responses API, and Anthropic formats.
    """
    tool_call_ids: list[str] = []

    # OpenAI Responses API: function_call_output items
    if entry.get("type") == "function_call_output":
        if call_id := entry.get("call_id"):
            tool_call_ids.append(str(call_id))
        return tool_call_ids

    # OpenAI Chat Completions: a tool response message with role "tool".
    if entry.get("role") == "tool":
        if tool_call_id := entry.get("tool_call_id"):
            tool_call_ids.append(str(tool_call_id))

    # Anthropic: check content items for tool_result type.
    if entry.get("role") == "user":
        content = entry.get("content")
        if isinstance(content, list):
            for item in content:
                if item.get("type") != "tool_result":
                    continue
                if tool_call_id := item.get("tool_use_id"):
                    tool_call_ids.append(tool_call_id)

    return tool_call_ids