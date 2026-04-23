def _combine_tool_responses(tool_outputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Combine multiple Anthropic tool responses into a single user message.
    For non-Anthropic formats, returns the original list unchanged.
    """
    if len(tool_outputs) <= 1:
        return tool_outputs

    # Anthropic responses have role="user", type="message", and content is a list with tool_result items
    anthropic_responses = [
        output
        for output in tool_outputs
        if (
            output.get("role") == "user"
            and output.get("type") == "message"
            and isinstance(output.get("content"), list)
            and any(
                item.get("type") == "tool_result"
                for item in output.get("content", [])
                if isinstance(item, dict)
            )
        )
    ]

    if len(anthropic_responses) > 1:
        combined_content = [
            item for response in anthropic_responses for item in response["content"]
        ]

        combined_response = {
            "role": "user",
            "type": "message",
            "content": combined_content,
        }

        non_anthropic_responses = [
            output for output in tool_outputs if output not in anthropic_responses
        ]

        return [combined_response] + non_anthropic_responses

    return tool_outputs