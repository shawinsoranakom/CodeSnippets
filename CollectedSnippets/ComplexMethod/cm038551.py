def parse_message_from_completion_text(text: str, thinking_mode: str):
    summary_content, reasoning, tool_calls = "", "", []
    index, stop_token = 0, None
    tool_calls_start_token = f"\n\n<{dsml_token}function_calls"

    is_thinking, is_tool_calling = thinking_mode == "thinking", False

    if is_thinking:
        index, content_delta, stop_token = _read_until_stop(
            index, text, [thinking_end_token, tool_calls_start_token]
        )
        reasoning = content_delta
        if stop_token != thinking_end_token:
            raise RuntimeError("Invalid thinking format")

    index, content_delta, stop_token = _read_until_stop(
        index, text, [eos_token, tool_calls_start_token]
    )
    summary_content = content_delta
    if stop_token == tool_calls_start_token:
        is_tool_calling = True
    else:
        if stop_token != eos_token:
            raise RuntimeError("Invalid summary format")

    if is_tool_calling:
        index, stop_token, tool_calls = parse_tool_calls(index, text)

        index, tool_ends_text, stop_token = _read_until_stop(index, text, [eos_token])
        if tool_ends_text:
            raise RuntimeError("Unexpected content after tool calls")

    if not (len(text) == index and stop_token in [eos_token, None]):
        raise RuntimeError("Unexpected content at end")

    for sp_token in [
        bos_token,
        eos_token,
        thinking_start_token,
        thinking_end_token,
        dsml_token,
    ]:
        if sp_token in summary_content or sp_token in reasoning:
            raise RuntimeError("Unexpected special token in content")

    return {
        "role": "assistant",
        "content": summary_content,
        "reasoning": reasoning,
        "tool_calls": tool_calls_to_openai_format(tool_calls),
    }