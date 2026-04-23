def _parse_chat_message_content(
    message: ChatCompletionMessageParam,
    mm_tracker: BaseMultiModalItemTracker,
    content_format: ChatTemplateContentFormat,
    interleave_strings: bool,
    mm_processor_kwargs: dict[str, Any] | None = None,
) -> list[ConversationMessage]:
    role = message["role"]
    content = message.get("content")
    reasoning = message.get("reasoning")

    if content is None:
        content = []
    elif isinstance(content, str):
        content = [ChatCompletionContentPartTextParam(type="text", text=content)]
    result = _parse_chat_message_content_parts(
        role,
        content,  # type: ignore
        mm_tracker,
        wrap_dicts=(content_format == "openai"),
        interleave_strings=interleave_strings,
        mm_processor_kwargs=mm_processor_kwargs,
    )

    for result_msg in result:
        if role == "assistant":
            parsed_msg = _AssistantParser(message)

            # The 'tool_calls' is not None check ensures compatibility.
            # It's needed only if downstream code doesn't strictly
            # follow the OpenAI spec.
            if "tool_calls" in parsed_msg and parsed_msg["tool_calls"] is not None:
                result_msg["tool_calls"] = list(parsed_msg["tool_calls"])
            # Include reasoning if present for interleaved thinking.
            if reasoning is not None:
                result_msg["reasoning"] = cast(str, reasoning)
                result_msg["reasoning_content"] = cast(
                    str, reasoning
                )  # keep compatibility
        elif role == "tool":
            parsed_msg = _ToolParser(message)
            if "tool_call_id" in parsed_msg:
                result_msg["tool_call_id"] = parsed_msg["tool_call_id"]
            # Normalize tool message content from OpenAI array format to plain
            # string. Clients like Claude Code / Cursor send tool results as
            # [{"type": "text", "text": "..."}], but most chat templates only
            # handle string content for tool messages.
            msg_content = result_msg.get("content")
            if isinstance(msg_content, list):
                texts = [
                    item.get("text", "")
                    for item in msg_content
                    if isinstance(item, dict) and item.get("type") == "text"
                ]
                result_msg["content"] = "\n".join(texts) if texts else ""

        if "name" in message and isinstance(message["name"], str):
            result_msg["name"] = message["name"]

        if role == "developer":
            result_msg["tools"] = message.get("tools", None)
    return result