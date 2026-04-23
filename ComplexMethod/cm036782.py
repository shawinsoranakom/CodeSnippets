async def accumulate_streaming_response(
    stream_generator: AsyncGenerator[str, None],
) -> ChatCompletionResponse:
    """
    Accumulate streaming SSE chunks into a complete ChatCompletionResponse.

    This helper parses the SSE format and builds up the complete response
    by combining all the delta chunks.
    """
    accumulated_content = ""
    accumulated_reasoning = None
    accumulated_tool_calls: list[dict[str, Any]] = []
    role = None
    finish_reason = None
    response_id = None
    created = None
    model = None
    index = 0

    async for chunk_str in stream_generator:
        # Skip empty lines and [DONE] marker
        if not chunk_str.strip() or chunk_str.strip() == "data: [DONE]":
            continue

        # Parse SSE format: "data: {json}\n\n"
        if chunk_str.startswith("data: "):
            json_str = chunk_str[6:].strip()
            try:
                chunk_data = json.loads(json_str)
                # print(f"DEBUG: Parsed chunk_data: {chunk_data}")
                chunk = ChatCompletionStreamResponse(**chunk_data)

                # Store metadata from first chunk
                if response_id is None:
                    response_id = chunk.id
                    created = chunk.created
                    model = chunk.model

                # Process each choice in the chunk
                for choice in chunk.choices:
                    if choice.delta.role:
                        role = choice.delta.role
                    if choice.delta.content:
                        accumulated_content += choice.delta.content
                    if choice.delta.reasoning:
                        if accumulated_reasoning is None:
                            accumulated_reasoning = ""
                        accumulated_reasoning += choice.delta.reasoning
                    if choice.delta.tool_calls:
                        # Accumulate tool calls
                        for tool_call_delta in choice.delta.tool_calls:
                            # Find or create the tool call at this index
                            while len(accumulated_tool_calls) <= tool_call_delta.index:
                                accumulated_tool_calls.append(
                                    {
                                        "id": None,
                                        "type": "function",
                                        "function": {"name": "", "arguments": ""},
                                    }
                                )

                            if tool_call_delta.id:
                                accumulated_tool_calls[tool_call_delta.index]["id"] = (
                                    tool_call_delta.id
                                )
                            if tool_call_delta.function:
                                if tool_call_delta.function.name:
                                    accumulated_tool_calls[tool_call_delta.index][
                                        "function"
                                    ]["name"] += tool_call_delta.function.name
                                if tool_call_delta.function.arguments:
                                    accumulated_tool_calls[tool_call_delta.index][
                                        "function"
                                    ]["arguments"] += tool_call_delta.function.arguments

                    if choice.finish_reason:
                        finish_reason = choice.finish_reason
                    if choice.index is not None:
                        index = choice.index

            except json.JSONDecodeError:
                continue

    # Build the final message
    message_kwargs = {
        "role": role or "assistant",
        "content": accumulated_content if accumulated_content else None,
        "reasoning": accumulated_reasoning,
    }

    # Only include tool_calls if there are any
    if accumulated_tool_calls:
        message_kwargs["tool_calls"] = [
            {"id": tc["id"], "type": tc["type"], "function": tc["function"]}
            for tc in accumulated_tool_calls
        ]

    message = ChatMessage(**message_kwargs)

    # Build the final response
    choice = ChatCompletionResponseChoice(
        index=index,
        message=message,
        finish_reason=finish_reason or "stop",
    )

    # Create usage info (with dummy values for tests)
    usage = UsageInfo(
        prompt_tokens=0,
        completion_tokens=0,
        total_tokens=0,
    )

    response = ChatCompletionResponse(
        id=response_id or "chatcmpl-test",
        object="chat.completion",
        created=created or 0,
        model=model or "test-model",
        choices=[choice],
        usage=usage,
    )

    return response