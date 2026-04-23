def _extract_tool_call_ids_from_message(msg: dict) -> set[str]:
    """
    Extract tool_call IDs from an assistant message.

    Supports all formats:
    - OpenAI Chat Completions: {"role": "assistant", "tool_calls": [{"id": "..."}]}
    - Anthropic: {"role": "assistant", "content": [{"type": "tool_use", "id": "..."}]}
    - OpenAI Responses API: {"type": "function_call", "call_id": "..."}

    Returns:
        Set of tool_call IDs found in the message.
    """
    ids: set[str] = set()

    # Responses API: standalone function_call item
    if msg.get("type") == "function_call":
        if call_id := msg.get("call_id"):
            ids.add(call_id)
        return ids

    if msg.get("role") != "assistant":
        return ids

    # OpenAI Chat Completions format: tool_calls array
    if msg.get("tool_calls"):
        for tc in msg["tool_calls"]:
            tc_id = tc.get("id")
            if tc_id:
                ids.add(tc_id)

    # Anthropic format: content list with tool_use blocks
    content = msg.get("content")
    if isinstance(content, list):
        for block in content:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tc_id = block.get("id")
                if tc_id:
                    ids.add(tc_id)

    return ids