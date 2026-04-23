def parse_chat_input_to_harmony_message(
    chat_msg, tool_id_names: dict[str, str] | None = None
) -> list[Message]:
    """
    Parse a message from request.messages in the Chat Completion API to
    Harmony messages.
    """
    tool_id_names = tool_id_names or {}

    if not isinstance(chat_msg, dict):
        # Handle Pydantic models
        chat_msg = chat_msg.model_dump(exclude_none=True)

    role = chat_msg.get("role")
    msgs: list[Message] = []

    # Assistant message with tool calls
    tool_calls = chat_msg.get("tool_calls", [])

    if role == "assistant" and tool_calls:
        content = flatten_chat_text_content(chat_msg.get("content"))
        if content:
            commentary_msg = Message.from_role_and_content(Role.ASSISTANT, content)
            commentary_msg = commentary_msg.with_channel("commentary")
            msgs.append(commentary_msg)

        reasoning = chat_msg.get("reasoning")
        if reasoning:
            analysis_msg = Message.from_role_and_content(Role.ASSISTANT, reasoning)
            analysis_msg = analysis_msg.with_channel("analysis")
            msgs.append(analysis_msg)

        for call in tool_calls:
            func = call.get("function", {})
            name = func.get("name", "")
            arguments = func.get("arguments", "") or ""
            msg = Message.from_role_and_content(Role.ASSISTANT, arguments)
            msg = msg.with_channel("commentary")
            msg = msg.with_recipient(f"functions.{name}")
            # Officially, this should be `<|constrain|>json` but there is not clear
            # evidence that improves accuracy over `json` and some anecdotes to the
            # contrary. Further testing of the different content_types is needed.
            msg = msg.with_content_type("json")
            msgs.append(msg)
        return msgs

    # Tool role message (tool output)
    if role == "tool":
        tool_call_id = chat_msg.get("tool_call_id", "")
        name = tool_id_names.get(tool_call_id, "")
        content = chat_msg.get("content", "") or ""
        content = flatten_chat_text_content(content)

        msg = (
            Message.from_author_and_content(
                Author.new(Role.TOOL, f"functions.{name}"), content
            )
            .with_channel("commentary")
            .with_recipient("assistant")
        )
        return [msg]

    # Non-tool reasoning content
    reasoning = chat_msg.get("reasoning")
    if role == "assistant" and reasoning:
        analysis_msg = Message.from_role_and_content(Role.ASSISTANT, reasoning)
        analysis_msg = analysis_msg.with_channel("analysis")
        msgs.append(analysis_msg)

    # Default: user/assistant/system messages with content
    content = chat_msg.get("content") or ""
    if content is None:
        content = ""
    if isinstance(content, str):
        contents = [TextContent(text=content)]
    else:
        # TODO: Support refusal.
        contents = [TextContent(text=c.get("text", "")) for c in content]

    # Only add assistant messages if they have content, as reasoning or tool calling
    # assistant messages were already added above.
    if role == "assistant" and contents and contents[0].text:
        msg = Message.from_role_and_contents(role, contents)
        # Send non-tool assistant messages to the final channel
        msg = msg.with_channel("final")
        msgs.append(msg)
    # For user/system/developer messages, add them directly even if no content.
    elif role != "assistant":
        msg = Message.from_role_and_contents(role, contents)
        msgs.append(msg)

    return msgs