async def test_streaming_tool_usage_with_arguments(provider: str) -> None:
    """
    Test reading streaming tool usage response with arguments.
    In that case `input` in initial `tool_use` chunk is `{}` but subsequent `partial_json` chunks make up the actual
    complete input value.
    """
    client = get_client_or_skip(provider)

    # Define tools
    add_numbers = FunctionTool(_add_numbers, description="Add two numbers together", name="add_numbers")

    chunks: List[str | CreateResult] = []
    async for chunk in client.create_stream(
        messages=[
            SystemMessage(content="Use the tools to evaluate calculations"),
            UserMessage(content="2 + 2", source="user"),
        ],
        tools=[add_numbers],
        tool_choice="required",
    ):
        chunks.append(chunk)

    assert len(chunks) > 0
    assert isinstance(chunks[-1], CreateResult)
    result: CreateResult = chunks[-1]
    assert len(result.content) == 1
    content = result.content[-1]
    assert isinstance(content, FunctionCall)
    assert content.name == "add_numbers"
    assert json.loads(content.arguments) is not None