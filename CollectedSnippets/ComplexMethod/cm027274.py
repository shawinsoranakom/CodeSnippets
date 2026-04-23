async def _transform_stream(
    result: AsyncIterator[ollama.ChatResponse],
) -> AsyncGenerator[conversation.AssistantContentDeltaDict]:
    """Transform the response stream into HA format.

    An Ollama streaming response may come in chunks like this:

    response: message=Message(role="assistant", content="Paris")
    response: message=Message(role="assistant", content=".")
    response: message=Message(role="assistant", content=""), done: True, done_reason: "stop"
    response: message=Message(role="assistant", tool_calls=[...])
    response: message=Message(role="assistant", content=""), done: True, done_reason: "stop"

    This generator conforms to the chatlog delta stream expectations in that it
    yields deltas, then the role only once the response is done.
    """

    new_msg = True
    async for response in result:
        _LOGGER.debug("Received response: %s", response)
        response_message = response["message"]
        chunk: conversation.AssistantContentDeltaDict = {}
        if new_msg:
            new_msg = False
            chunk["role"] = "assistant"
        if (tool_calls := response_message.get("tool_calls")) is not None:
            chunk["tool_calls"] = [
                llm.ToolInput(
                    tool_name=tool_call["function"]["name"],
                    tool_args=_parse_tool_args(tool_call["function"]["arguments"]),
                )
                for tool_call in tool_calls
            ]
        if (content := response_message.get("content")) is not None:
            chunk["content"] = content
        if (thinking := response_message.get("thinking")) is not None:
            chunk["thinking_content"] = thinking
        if response_message.get("done"):
            new_msg = True
        yield chunk