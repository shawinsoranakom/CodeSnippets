def _convert_content(
    chat_content: (
        conversation.Content
        | conversation.ToolResultContent
        | conversation.AssistantContent
    ),
) -> ollama.Message:
    """Create tool response content."""
    if isinstance(chat_content, conversation.ToolResultContent):
        return ollama.Message(
            role=MessageRole.TOOL.value,
            content=json_dumps(chat_content.tool_result),
        )
    if isinstance(chat_content, conversation.AssistantContent):
        return ollama.Message(
            role=MessageRole.ASSISTANT.value,
            content=chat_content.content,
            thinking=chat_content.thinking_content,
            tool_calls=[
                ollama.Message.ToolCall(
                    function=ollama.Message.ToolCall.Function(
                        name=tool_call.tool_name,
                        arguments=tool_call.tool_args,
                    )
                )
                for tool_call in chat_content.tool_calls or ()
            ]
            or None,
        )
    if isinstance(chat_content, conversation.UserContent):
        images: list[ollama.Image] = []
        for attachment in chat_content.attachments or ():
            if not attachment.mime_type.startswith("image/"):
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="unsupported_attachment_type",
                )
            images.append(ollama.Image(value=attachment.path))
        return ollama.Message(
            role=MessageRole.USER.value,
            content=chat_content.content,
            images=images or None,
        )
    if isinstance(chat_content, conversation.SystemContent):
        return ollama.Message(
            role=MessageRole.SYSTEM.value,
            content=chat_content.content,
        )
    raise TypeError(f"Unexpected content type: {type(chat_content)}")