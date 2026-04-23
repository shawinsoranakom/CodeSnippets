async def test_anthropic_tool_choice_with_actual_api() -> None:
    """Test tool_choice parameter with actual Anthropic API endpoints."""
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

    # Test 1: tool_choice with specific tool
    messages: List[LLMMessage] = [
        SystemMessage(content="Use the tools as needed to help the user."),
        UserMessage(content="Process the text 'hello world' using the process_text tool.", source="user"),
    ]

    result = await client.create(
        messages=messages,
        tools=[pass_tool, add_tool],
        tool_choice=pass_tool,  # Force use of specific tool
    )

    # Verify we got a tool call for the specified tool
    assert isinstance(result.content, list)
    assert len(result.content) >= 1
    assert isinstance(result.content[0], FunctionCall)
    assert result.content[0].name == "process_text"

    # Test 2: tool_choice="auto" with tools
    auto_messages: List[LLMMessage] = [
        SystemMessage(content="Use the tools as needed to help the user."),
        UserMessage(content="Add the numbers 5 and 3.", source="user"),
    ]

    auto_result = await client.create(
        messages=auto_messages,
        tools=[pass_tool, add_tool],
        tool_choice="auto",  # Let model choose
    )

    # Should get a tool call, likely for add_numbers
    assert isinstance(auto_result.content, list)
    assert len(auto_result.content) >= 1
    assert isinstance(auto_result.content[0], FunctionCall)
    # Model should choose add_numbers for addition task
    assert auto_result.content[0].name == "add_numbers"

    # Test 3: No tools provided - should not include tool_choice in API call
    no_tools_messages: List[LLMMessage] = [
        UserMessage(content="What is the capital of France?", source="user"),
    ]

    no_tools_result = await client.create(messages=no_tools_messages)

    # Should get a text response without tool calls
    assert isinstance(no_tools_result.content, str)
    assert "paris" in no_tools_result.content.lower()

    # Test 4: tool_choice="required" with tools
    required_messages: List[LLMMessage] = [
        SystemMessage(content="You must use one of the available tools to help the user."),
        UserMessage(content="Help me with something.", source="user"),
    ]

    required_result = await client.create(
        messages=required_messages,
        tools=[pass_tool, add_tool],
        tool_choice="required",  # Force tool usage
    )

    # Should get a tool call (model forced to use a tool)
    assert isinstance(required_result.content, list)
    assert len(required_result.content) >= 1
    assert isinstance(required_result.content[0], FunctionCall)