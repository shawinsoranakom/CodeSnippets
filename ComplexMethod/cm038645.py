def _parse_chat_format_message(chat_msg: dict) -> list[Message]:
    """Parse an OpenAI chat-format dict into Harmony messages."""
    role = chat_msg.get("role")
    if role is None:
        raise ValueError(f"Message has no 'role' key: {chat_msg}")

    # Assistant message with tool calls
    tool_calls = chat_msg.get("tool_calls")
    if role == "assistant" and tool_calls:
        msgs: list[Message] = []
        for call in tool_calls:
            func = call.get("function", {})
            name = func.get("name", "")
            arguments = func.get("arguments", "") or ""
            msg = Message.from_role_and_content(Role.ASSISTANT, arguments)
            msg = msg.with_channel("commentary")
            msg = msg.with_recipient(f"functions.{name}")
            msg = msg.with_content_type("json")
            msgs.append(msg)
        return msgs

    # Tool role message (tool output)
    if role == "tool":
        name = chat_msg.get("name", "")
        if name and not name.startswith("functions."):
            name = f"functions.{name}"
        content = chat_msg.get("content", "") or ""
        content = flatten_chat_text_content(content)
        # NOTE: .with_recipient("assistant") is required on tool messages
        # to match parse_chat_input_to_harmony_message behavior and ensure
        # proper routing in the Harmony protocol.
        msg = (
            Message.from_author_and_content(Author.new(Role.TOOL, name), content)
            .with_channel("commentary")
            .with_recipient("assistant")
        )
        return [msg]

    # Default: user/assistant/system messages
    content = chat_msg.get("content", "")
    if isinstance(content, str):
        contents = [TextContent(text=content)]
    else:
        # TODO: Support refusal.
        contents = [TextContent(text=c.get("text", "")) for c in content]
    msg = Message.from_role_and_contents(role, contents)
    return [msg]