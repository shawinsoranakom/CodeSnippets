def _convert_message_to_dict(message: BaseMessage) -> dict[str, Any]:  # noqa: C901, PLR0912
    """Convert a LangChain message to an OpenRouter-compatible dict payload.

    Handles role mapping, multimodal content formatting, tool call
    serialization, and reasoning content preservation for multi-turn
    conversations.

    Args:
        message: The LangChain message.

    Returns:
        A dict suitable for the OpenRouter chat API `messages` parameter.
    """
    message_dict: dict[str, Any]
    if isinstance(message, ChatMessage):
        message_dict = {"role": message.role, "content": message.content}
    elif isinstance(message, HumanMessage):
        message_dict = {
            "role": "user",
            "content": _format_message_content(message.content),
        }
    elif isinstance(message, AIMessage):
        message_dict = {"role": "assistant", "content": message.content}
        # Filter out non-text blocks from list content
        if isinstance(message.content, list):
            text_blocks = [
                block
                for block in message.content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            message_dict["content"] = text_blocks or ""
        if message.tool_calls or message.invalid_tool_calls:
            message_dict["tool_calls"] = [
                _lc_tool_call_to_openrouter_tool_call(tc) for tc in message.tool_calls
            ] + [
                _lc_invalid_tool_call_to_openrouter_tool_call(tc)
                for tc in message.invalid_tool_calls
            ]
            if message_dict["content"] == "" or (
                isinstance(message_dict["content"], list)
                and not message_dict["content"]
            ):
                message_dict["content"] = None
        elif "tool_calls" in message.additional_kwargs:
            message_dict["tool_calls"] = message.additional_kwargs["tool_calls"]
            if message_dict["content"] == "" or (
                isinstance(message_dict["content"], list)
                and not message_dict["content"]
            ):
                message_dict["content"] = None
        # Preserve reasoning content for multi-turn conversations (e.g.
        # tool-calling loops). OpenRouter stores reasoning in "reasoning" and
        # optional structured details in "reasoning_details".
        if "reasoning_content" in message.additional_kwargs:
            message_dict["reasoning"] = message.additional_kwargs["reasoning_content"]
        if "reasoning_details" in message.additional_kwargs:
            message_dict["reasoning_details"] = message.additional_kwargs[
                "reasoning_details"
            ]
    elif isinstance(message, SystemMessage):
        message_dict = {"role": "system", "content": message.content}
    elif isinstance(message, ToolMessage):
        message_dict = {
            "role": "tool",
            "content": message.content,
            "tool_call_id": message.tool_call_id,
        }
    else:
        msg = f"Got unknown type {message}"
        raise TypeError(msg)
    if "name" in message.additional_kwargs:
        message_dict["name"] = message.additional_kwargs["name"]
    return message_dict