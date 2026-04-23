def _truncate_tool_message_content(msg: dict, enc, max_tokens: int) -> None:
    """
    Carefully truncate tool message content while preserving tool structure.
    Handles Anthropic, Chat Completions, and Responses API tool messages.
    """
    # Responses API: function_call_output has "output" field
    if msg.get("type") == "function_call_output":
        output = msg.get("output", "")
        if isinstance(output, str) and _tok_len(output, enc) > max_tokens:
            msg["output"] = _truncate_middle_tokens(output, enc, max_tokens)
        return

    content = msg.get("content")

    # OpenAI Chat Completions tool message: role="tool" with string content
    if msg.get("role") == "tool" and isinstance(content, str):
        if _tok_len(content, enc) > max_tokens:
            msg["content"] = _truncate_middle_tokens(content, enc, max_tokens)
        return

    # Anthropic-style: list content with tool_result items
    if not isinstance(content, list):
        return

    for item in content:
        # Only process tool_result items, leave tool_use blocks completely intact
        if not (isinstance(item, dict) and item.get("type") == "tool_result"):
            continue

        result_content = item.get("content", "")
        if (
            isinstance(result_content, str)
            and _tok_len(result_content, enc) > max_tokens
        ):
            item["content"] = _truncate_middle_tokens(result_content, enc, max_tokens)