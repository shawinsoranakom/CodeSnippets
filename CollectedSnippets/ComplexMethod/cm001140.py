def _msg_tokens(msg: dict, enc) -> int:
    """
    OpenAI counts ≈3 wrapper tokens per chat message, plus 1 if "name"
    is present, plus the tokenised content length.
    For tool calls, we need to count tokens in tool_calls and content fields.
    Supports Chat Completions, Anthropic, and Responses API formats.
    """
    WRAPPER = 3 + (1 if "name" in msg else 0)

    # Responses API: function_call items have arguments + name
    if msg.get("type") == "function_call":
        return (
            WRAPPER
            + _tok_len(msg.get("name", ""), enc)
            + _tok_len(msg.get("arguments", ""), enc)
            + _tok_len(msg.get("call_id", ""), enc)
        )

    # Responses API: function_call_output items have output
    if msg.get("type") == "function_call_output":
        return (
            WRAPPER
            + _tok_len(msg.get("output", ""), enc)
            + _tok_len(msg.get("call_id", ""), enc)
        )

    # Count content tokens
    content_tokens = _tok_len(msg.get("content") or "", enc)

    # Count tool call tokens for both OpenAI and Anthropic formats
    tool_call_tokens = 0

    # OpenAI Chat Completions format: tool_calls array at message level
    if "tool_calls" in msg and isinstance(msg["tool_calls"], list):
        for tool_call in msg["tool_calls"]:
            # Count the tool call structure tokens
            tool_call_tokens += _tok_len(tool_call.get("id", ""), enc)
            tool_call_tokens += _tok_len(tool_call.get("type", ""), enc)
            if "function" in tool_call:
                tool_call_tokens += _tok_len(tool_call["function"].get("name", ""), enc)
                tool_call_tokens += _tok_len(
                    tool_call["function"].get("arguments", ""), enc
                )

    # Anthropic format: tool_use within content array
    content = msg.get("content")
    if isinstance(content, list):
        for item in content:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                # Count the tool use structure tokens
                tool_call_tokens += _tok_len(item.get("id", ""), enc)
                tool_call_tokens += _tok_len(item.get("name", ""), enc)
                tool_call_tokens += _tok_len(json.dumps(item.get("input", {})), enc)
            elif isinstance(item, dict) and item.get("type") == "tool_result":
                # Count tool result tokens
                tool_call_tokens += _tok_len(item.get("tool_use_id", ""), enc)
                tool_call_tokens += _tok_len(item.get("content", ""), enc)
            elif isinstance(item, dict) and item.get("type") == "text":
                # Count text block tokens (standard: "text" key, fallback: "content")
                text_val = item.get("text") or item.get("content", "")
                tool_call_tokens += _tok_len(text_val, enc)
            elif isinstance(item, dict) and "content" in item:
                # Other content types with content field
                tool_call_tokens += _tok_len(item.get("content", ""), enc)
        # For list content, override content_tokens since we counted everything above
        content_tokens = 0

    return WRAPPER + content_tokens + tool_call_tokens