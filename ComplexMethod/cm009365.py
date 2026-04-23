def _convert_message_to_dict(message: BaseMessage) -> dict:
    """Convert a LangChain message to a dictionary.

    Args:
        message: The LangChain message.

    Returns:
        The dictionary.

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
        # Translate v1 content
        if message.response_metadata.get("output_version") == "v1":
            new_content, new_additional_kwargs = _convert_from_v1_to_groq(
                message.content_blocks, message.response_metadata.get("model_provider")
            )
            message = message.model_copy(
                update={
                    "content": new_content,
                    "additional_kwargs": new_additional_kwargs,
                }
            )
        message_dict = {"role": "assistant", "content": message.content}

        # If content is a list of content blocks, filter out tool_call blocks
        # as Groq API only accepts 'text' type blocks in content
        if isinstance(message.content, list):
            text_blocks = [
                block
                for block in message.content
                if isinstance(block, dict) and block.get("type") == "text"
            ]
            message_dict["content"] = text_blocks or ""

        if "function_call" in message.additional_kwargs:
            message_dict["function_call"] = message.additional_kwargs["function_call"]
            # If function call only, content is None not empty string
            if message_dict["content"] == "":
                message_dict["content"] = None
        if message.tool_calls or message.invalid_tool_calls:
            message_dict["tool_calls"] = [
                _lc_tool_call_to_groq_tool_call(tc) for tc in message.tool_calls
            ] + [
                _lc_invalid_tool_call_to_groq_tool_call(tc)
                for tc in message.invalid_tool_calls
            ]
            # If tool calls only (no text blocks), content is None not empty string
            if message_dict["content"] == "" or (
                isinstance(message_dict["content"], list)
                and not message_dict["content"]
            ):
                message_dict["content"] = None
        elif "tool_calls" in message.additional_kwargs:
            message_dict["tool_calls"] = message.additional_kwargs["tool_calls"]
            # If tool calls only, content is None not empty string
            if message_dict["content"] == "" or (
                isinstance(message_dict["content"], list)
                and not message_dict["content"]
            ):
                message_dict["content"] = None
    elif isinstance(message, SystemMessage):
        message_dict = {"role": "system", "content": message.content}
    elif isinstance(message, FunctionMessage):
        message_dict = {
            "role": "function",
            "content": message.content,
            "name": message.name,
        }
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