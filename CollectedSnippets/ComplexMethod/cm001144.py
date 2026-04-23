def _extract_tool_response_ids_from_message(msg: dict) -> set[str]:
    """
    Extract tool_call IDs that this message is responding to.

    Supports all formats:
    - OpenAI Chat Completions: {"role": "tool", "tool_call_id": "..."}
    - Anthropic: {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "..."}]}
    - OpenAI Responses API: {"type": "function_call_output", "call_id": "..."}

    Returns:
        Set of tool_call IDs this message responds to.
    """
    ids: set[str] = set()

    # Responses API: standalone function_call_output item
    if msg.get("type") == "function_call_output":
        if call_id := msg.get("call_id"):
            ids.add(call_id)
        return ids

    # OpenAI Chat Completions format: role=tool with tool_call_id
    if msg.get("role") == "tool":
        tc_id = msg.get("tool_call_id")
        if tc_id:
            ids.add(tc_id)

    # Anthropic format: content list with tool_result blocks
    content = msg.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_result":
                tc_id = block.get("tool_use_id")
                if tc_id:
                    ids.add(tc_id)

    return ids