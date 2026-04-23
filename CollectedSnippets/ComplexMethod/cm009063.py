def _convert_message_to_mistral_chat_message(
    message: BaseMessage,
) -> dict:
    if isinstance(message, ChatMessage):
        return {"role": message.role, "content": message.content}
    if isinstance(message, HumanMessage):
        return {"role": "user", "content": message.content}
    if isinstance(message, AIMessage):
        message_dict: dict[str, Any] = {"role": "assistant"}
        tool_calls: list = []
        if message.tool_calls or message.invalid_tool_calls:
            if message.tool_calls:
                tool_calls.extend(
                    _format_tool_call_for_mistral(tool_call)
                    for tool_call in message.tool_calls
                )
            if message.invalid_tool_calls:
                tool_calls.extend(
                    _format_invalid_tool_call_for_mistral(invalid_tool_call)
                    for invalid_tool_call in message.invalid_tool_calls
                )
        elif "tool_calls" in message.additional_kwargs:
            for tc in message.additional_kwargs["tool_calls"]:
                chunk = {
                    "function": {
                        "name": tc["function"]["name"],
                        "arguments": tc["function"]["arguments"],
                    }
                }
                if _id := tc.get("id"):
                    chunk["id"] = _id
                tool_calls.append(chunk)
        else:
            pass
        if tool_calls:  # do not populate empty list tool_calls
            message_dict["tool_calls"] = tool_calls

        # Message content
        # Translate v1 content
        if message.response_metadata.get("output_version") == "v1":
            content = _convert_from_v1_to_mistral(
                message.content_blocks, message.response_metadata.get("model_provider")
            )
        else:
            content = message.content

        if tool_calls and content:
            # Assistant message must have either content or tool_calls, but not both.
            # Some providers may not support tool_calls in the same message as content.
            # This is done to ensure compatibility with messages from other providers.
            content = ""

        elif isinstance(content, list):
            content = [
                _clean_block(block)
                if isinstance(block, dict) and "index" in block
                else block
                for block in content
            ]
        else:
            content = message.content

        # if any blocks are dicts, cast strings to text blocks
        if any(isinstance(block, dict) for block in content):
            content = [
                block if isinstance(block, dict) else {"type": "text", "text": block}
                for block in content
            ]
        message_dict["content"] = content

        if "prefix" in message.additional_kwargs:
            message_dict["prefix"] = message.additional_kwargs["prefix"]
        return message_dict
    if isinstance(message, SystemMessage):
        return {"role": "system", "content": message.content}
    if isinstance(message, ToolMessage):
        return {
            "role": "tool",
            "content": message.content,
            "name": message.name,
            "tool_call_id": _convert_tool_call_id_to_mistral_compatible(
                message.tool_call_id
            ),
        }
    msg = f"Got unknown type {message}"
    raise ValueError(msg)