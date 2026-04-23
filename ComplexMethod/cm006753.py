async def handle_on_chain_stream(
    event: dict[str, Any],
    agent_message: Message,
    send_message_callback: SendMessageFunctionType,  # noqa: ARG001
    send_token_callback: OnTokenFunctionType | None,
    start_time: float,
    *,
    had_streaming: bool = False,  # noqa: ARG001
    message_id: str | None = None,
) -> tuple[Message, float]:
    data_chunk = event["data"].get("chunk", {})
    if isinstance(data_chunk, dict) and data_chunk.get("output"):
        output = data_chunk.get("output")
        if output and isinstance(output, str | list):
            agent_message.text = _extract_output_text(output)
        agent_message.properties.state = "complete"
        # Don't call send_message_callback here - we must update in place
        # in order to keep the message id consistent throughout the stream.
        # The final message will be sent after the loop completes
        start_time = perf_counter()
    elif isinstance(data_chunk, AIMessageChunk):
        output_text = _extract_output_text(data_chunk.content)
        # For streaming, send token event if callback is available
        # Note: we should expect the callback, but we keep it optional for backwards compatibility
        # as of v1.6.5
        if output_text is not None and output_text != "" and send_token_callback and message_id:
            await asyncio.to_thread(
                send_token_callback,
                data={
                    "chunk": output_text,
                    "id": str(message_id),
                },
            )

        if not agent_message.text:
            # Starts the timer when the first message is starting to be generated
            start_time = perf_counter()
    return agent_message, start_time