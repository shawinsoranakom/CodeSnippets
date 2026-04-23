def _convert_content_to_chat_message(
    content: conversation.Content,
) -> ChatCompletionMessageParam | None:
    """Convert any native chat message for this agent to the native format."""
    LOGGER.debug("_convert_content_to_chat_message=%s", content)
    if isinstance(content, conversation.ToolResultContent):
        return ChatCompletionToolMessageParam(
            role="tool",
            tool_call_id=content.tool_call_id,
            content=json_dumps(content.tool_result),
        )

    role: Literal["user", "assistant", "system"] = content.role
    if role == "system" and content.content:
        return ChatCompletionSystemMessageParam(role="system", content=content.content)

    if role == "user" and content.content:
        return ChatCompletionUserMessageParam(role="user", content=content.content)

    if role == "assistant":
        param = ChatCompletionAssistantMessageParam(
            role="assistant",
            content=content.content,
        )
        if isinstance(content, conversation.AssistantContent) and content.tool_calls:
            param["tool_calls"] = [
                ChatCompletionMessageFunctionToolCallParam(
                    type="function",
                    id=tool_call.id,
                    function=Function(
                        arguments=json_dumps(tool_call.tool_args),
                        name=tool_call.tool_name,
                    ),
                )
                for tool_call in content.tool_calls
            ]
        return param
    LOGGER.warning("Could not convert message to Completions API: %s", content)
    return None