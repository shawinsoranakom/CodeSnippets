def _remove_orphan_tool_responses(
    messages: list[dict], orphan_ids: set[str]
) -> list[dict]:
    """
    Remove tool response messages/blocks that reference orphan tool_call IDs.

    Supports OpenAI Chat Completions, Anthropic, and Responses API formats.
    For Anthropic messages with mixed valid/orphan tool_result blocks,
    filters out only the orphan blocks instead of dropping the entire message.
    """
    result = []
    for msg in messages:
        # Responses API: function_call_output - drop if orphan
        if msg.get("type") == "function_call_output":
            if msg.get("call_id") in orphan_ids:
                continue
            result.append(msg)
            continue

        # OpenAI Chat Completions: role=tool - drop entire message if orphan
        if msg.get("role") == "tool":
            tc_id = msg.get("tool_call_id")
            if tc_id and tc_id in orphan_ids:
                continue
            result.append(msg)
            continue

        # Anthropic format: content list may have mixed tool_result blocks
        content = msg.get("content")
        if isinstance(content, list):
            has_tool_results = any(
                isinstance(b, dict) and b.get("type") == "tool_result" for b in content
            )
            if has_tool_results:
                # Filter out orphan tool_result blocks, keep valid ones
                filtered_content = [
                    block
                    for block in content
                    if not (
                        isinstance(block, dict)
                        and block.get("type") == "tool_result"
                        and block.get("tool_use_id") in orphan_ids
                    )
                ]
                # Only keep message if it has remaining content
                if filtered_content:
                    msg = msg.copy()
                    msg["content"] = filtered_content
                    result.append(msg)
                continue

        result.append(msg)
    return result