async def test_azure_ai_tool_choice_specific_tool_streaming(
    tool_choice_stream_client: AzureAIChatCompletionClient,
) -> None:
    """Test tool_choice parameter with streaming and a specific tool using mocks."""
    # Define tools
    pass_tool = FunctionTool(_pass_function, description="Process input text", name="process_text")
    add_tool = FunctionTool(_add_numbers, description="Add two numbers together", name="add_numbers")

    messages = [
        UserMessage(content="Process the text 'hello'.", source="user"),
    ]

    chunks: List[Union[str, CreateResult]] = []
    async for chunk in tool_choice_stream_client.create_stream(
        messages=messages,
        tools=[pass_tool, add_tool],
        tool_choice=pass_tool,  # Force use of specific tool
    ):
        chunks.append(chunk)

    # Verify that we got some result
    final_result = chunks[-1]
    assert isinstance(final_result, CreateResult)
    assert final_result.finish_reason == "function_calls"
    assert isinstance(final_result.content, list)
    assert len(final_result.content) == 1
    assert isinstance(final_result.content[0], FunctionCall)
    assert final_result.content[0].name == "process_text"
    assert final_result.content[0].arguments == '{"input": "hello"}'
    assert final_result.thought == "Let me process this for you."