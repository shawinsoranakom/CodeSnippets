def _parse_harmony_format_message(chat_msg: dict) -> Message:
    """Reconstruct a Message from Harmony-format dict,
    preserving channel, recipient, and content_type."""
    author_dict = chat_msg["author"]
    role = author_dict.get("role")
    name = author_dict.get("name")

    raw_content = chat_msg.get("content", "")
    if isinstance(raw_content, list):
        # TODO: Support refusal and non-text content types.
        contents = [TextContent(text=c.get("text", "")) for c in raw_content]
    elif isinstance(raw_content, str):
        contents = [TextContent(text=raw_content)]
    else:
        contents = [TextContent(text="")]

    if name:
        msg = Message.from_author_and_contents(Author.new(Role(role), name), contents)
    else:
        msg = Message.from_role_and_contents(Role(role), contents)

    channel = chat_msg.get("channel")
    if channel:
        msg = msg.with_channel(channel)
    recipient = chat_msg.get("recipient")
    if recipient:
        msg = msg.with_recipient(recipient)
    content_type = chat_msg.get("content_type")
    if content_type:
        msg = msg.with_content_type(content_type)

    return msg