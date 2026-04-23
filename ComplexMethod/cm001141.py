def _is_tool_message(msg: dict) -> bool:
    """Check if a message contains tool calls or results that should be protected."""
    # Responses API: standalone function_call / function_call_output items
    if msg.get("type") in ("function_call", "function_call_output"):
        return True

    content = msg.get("content")

    # Check for Anthropic-style tool messages
    if isinstance(content, list) and any(
        isinstance(item, dict) and item.get("type") in ("tool_use", "tool_result")
        for item in content
    ):
        return True

    # Check for OpenAI Chat Completions-style tool calls in the message
    if "tool_calls" in msg or msg.get("role") == "tool":
        return True

    return False