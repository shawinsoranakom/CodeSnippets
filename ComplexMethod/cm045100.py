async def test_streaming_tool_usage_with_no_arguments(provider: str) -> None:
    """
    Test reading streaming tool usage response with no arguments.
    In that case `input` in initial `tool_use` chunk is `{}` and subsequent `partial_json` chunks are empty.
    """
    client = get_client_or_skip(provider)

    # Define tools
    ask_for_input_tool = FunctionTool(
        _ask_for_input, description="Ask user for more input", name="ask_for_input", strict=True
    )

    chunks: List[str | CreateResult] = []
    async for chunk in client.create_stream(
        messages=[
            SystemMessage(content="When user intent is unclear, ask for more input"),
            UserMessage(content="Erm...", source="user"),
        ],
        tools=[ask_for_input_tool],
        tool_choice="required",
    ):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    result: CreateResult = chunks[-1]
    assert len(result.content) == 1
    content = result.content[-1]
    assert isinstance(content, FunctionCall)
    assert content.name == "ask_for_input"
    assert json.loads(content.arguments) is not None