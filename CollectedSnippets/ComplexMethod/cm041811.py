async def sampling_loop(
    *,
    model: str,
    provider: APIProvider,
    system_prompt_suffix: str,
    messages: list[BetaMessageParam],
    output_callback: Callable[[BetaContentBlock], None],
    tool_output_callback: Callable[[ToolResult, str], None],
    api_key: str,
    only_n_most_recent_images: int | None = None,
    max_tokens: int = 4096,
):
    """
    Agentic sampling loop for the assistant/tool interaction of computer use.
    """
    tool_collection = ToolCollection(
        ComputerTool(),
        # BashTool(),
        # EditTool(),
    )
    system = (
        f"{SYSTEM_PROMPT}{' ' + system_prompt_suffix if system_prompt_suffix else ''}"
    )

    while True:
        if only_n_most_recent_images:
            _maybe_filter_to_n_most_recent_images(messages, only_n_most_recent_images)

        if provider == APIProvider.ANTHROPIC:
            client = Anthropic(api_key=api_key)
        elif provider == APIProvider.VERTEX:
            client = AnthropicVertex()
        elif provider == APIProvider.BEDROCK:
            client = AnthropicBedrock()

        # Call the API
        # we use raw_response to provide debug information to streamlit. Your
        # implementation may be able call the SDK directly with:
        # `response = client.messages.create(...)` instead.
        raw_response = client.beta.messages.create(
            max_tokens=max_tokens,
            messages=messages,
            model=model,
            system=system,
            tools=tool_collection.to_params(),
            betas=["computer-use-2024-10-22"],
            stream=True,
        )

        response_content = []
        current_block = None

        for chunk in raw_response:
            if isinstance(chunk, BetaRawContentBlockStartEvent):
                current_block = chunk.content_block
            elif isinstance(chunk, BetaRawContentBlockDeltaEvent):
                if chunk.delta.type == "text_delta":
                    print(f"{chunk.delta.text}", end="", flush=True)
                    yield {"type": "chunk", "chunk": chunk.delta.text}
                    await asyncio.sleep(0)
                    if current_block and current_block.type == "text":
                        current_block.text += chunk.delta.text
                elif chunk.delta.type == "input_json_delta":
                    print(f"{chunk.delta.partial_json}", end="", flush=True)
                    if current_block and current_block.type == "tool_use":
                        if not hasattr(current_block, "partial_json"):
                            current_block.partial_json = ""
                        current_block.partial_json += chunk.delta.partial_json
            elif isinstance(chunk, BetaRawContentBlockStopEvent):
                if current_block:
                    if hasattr(current_block, "partial_json"):
                        # Finished a tool call
                        # print()
                        current_block.input = json.loads(current_block.partial_json)
                        # yield {"type": "chunk", "chunk": current_block.input}
                        delattr(current_block, "partial_json")
                    else:
                        # Finished a message
                        print("\n")
                        yield {"type": "chunk", "chunk": "\n"}
                        await asyncio.sleep(0)
                    response_content.append(current_block)
                    current_block = None

        response = BetaMessage(
            id=str(uuid.uuid4()),
            content=response_content,
            role="assistant",
            model=model,
            stop_reason=None,
            stop_sequence=None,
            type="message",
            usage={
                "input_tokens": 0,
                "output_tokens": 0,
            },  # Add a default usage dictionary
        )

        messages.append(
            {
                "role": "assistant",
                "content": cast(list[BetaContentBlockParam], response.content),
            }
        )

        tool_result_content: list[BetaToolResultBlockParam] = []
        for content_block in cast(list[BetaContentBlock], response.content):
            output_callback(content_block)
            if content_block.type == "tool_use":
                result = await tool_collection.run(
                    name=content_block.name,
                    tool_input=cast(dict[str, Any], content_block.input),
                )
                tool_result_content.append(
                    _make_api_tool_result(result, content_block.id)
                )
                tool_output_callback(result, content_block.id)

        if not tool_result_content:
            # Done!
            yield {"type": "messages", "messages": messages}
            break

        messages.append({"content": tool_result_content, "role": "user"})