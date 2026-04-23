async def test_anthropic_tool_choice_streaming_with_actual_api() -> None:
    """Test tool_choice parameter with streaming using actual Anthropic API endpoints."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not found in environment variables")

    client = AnthropicChatCompletionClient(
        model="claude-3-haiku-20240307",
        api_key=api_key,
    )

    # Define tools
    pass_tool = FunctionTool(_pass_function, description="Process input text", name="process_text")
    add_tool = FunctionTool(_add_numbers, description="Add two numbers together", name="add_numbers")

    # Test streaming with tool_choice
    messages: List[LLMMessage] = [
        SystemMessage(content="Use the tools as needed to help the user."),
        UserMessage(content="Process the text 'streaming test' using the process_text tool.", source="user"),
    ]

    chunks: List[str | CreateResult] = []
    async for chunk in client.create_stream(
        messages=messages,
        tools=[pass_tool, add_tool],
        tool_choice=pass_tool,  # Force use of specific tool
    ):
        chunks.append(chunk)

    # Verify we got chunks and a final result
    assert len(chunks) > 0
    final_result = chunks[-1]
    assert isinstance(final_result, CreateResult)

    # Should get a tool call for the specified tool
    assert isinstance(final_result.content, list)
    assert len(final_result.content) >= 1
    assert isinstance(final_result.content[0], FunctionCall)
    assert final_result.content[0].name == "process_text"

    # Test streaming without tools - should not include tool_choice
    no_tools_messages: List[LLMMessage] = [
        UserMessage(content="Tell me a short fact about cats.", source="user"),
    ]

    no_tools_chunks: List[str | CreateResult] = []
    async for chunk in client.create_stream(messages=no_tools_messages):
        no_tools_chunks.append(chunk)

    # Should get text response
    assert len(no_tools_chunks) > 0
    final_no_tools_result = no_tools_chunks[-1]
    assert isinstance(final_no_tools_result, CreateResult)
    assert isinstance(final_no_tools_result.content, str)
    assert len(final_no_tools_result.content) > 0