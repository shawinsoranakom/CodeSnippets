def _convert_message_to_openai_message(
    message: Union[TextMessage, MultiModalMessage, StopMessage, ToolCallSummaryMessage, HandoffMessage],
) -> OpenAIMessage:
    """Convert an AutoGen message to an OpenAI message format."""
    if isinstance(message, TextMessage):
        if message.source == "user":
            return {"role": "user", "content": str(message.content)}
        elif message.source == "system":
            return {"role": "system", "content": str(message.content)}
        elif message.source == "assistant":
            return {"role": "assistant", "content": str(message.content)}
        else:
            return {"role": "user", "content": str(message.content)}
    elif isinstance(message, MultiModalMessage):
        content_parts: List[Union[OpenAIMessageContent, OpenAIImageContent]] = []
        for part in message.content:
            if isinstance(part, TextMessage):
                content_parts.append({"type": "text", "text": str(part.content)})
            elif isinstance(part, ImageMessage):
                image_content = str(part.content)
                content_parts.append({"type": "image_url", "image_url": {"url": image_content}})
        return {"role": "user", "content": content_parts}
    else:
        return {"role": "user", "content": str(message.content)}