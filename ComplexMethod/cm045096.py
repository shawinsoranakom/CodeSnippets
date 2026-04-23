async def test_anthropic_tool_calling() -> None:
    """Test tool calling capabilities with Claude."""
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

    # Test tool calling with instruction to use specific tool
    messages: List[LLMMessage] = [
        SystemMessage(content="Use the tools available to help the user."),
        UserMessage(content="Process the text 'hello world' using the process_text tool.", source="user"),
    ]

    result = await client.create(messages=messages, tools=[pass_tool, add_tool])

    # Check that we got a tool call
    assert isinstance(result.content, list)
    assert len(result.content) >= 1
    assert isinstance(result.content[0], FunctionCall)

    # Check that the correct tool was called
    function_call = result.content[0]
    assert function_call.name == "process_text"

    # Test tool response handling
    messages.append(AssistantMessage(content=result.content, source="assistant"))
    messages.append(
        FunctionExecutionResultMessage(
            content=[
                FunctionExecutionResult(
                    content="Processed: hello world",
                    call_id=result.content[0].id,
                    is_error=False,
                    name=result.content[0].name,
                )
            ]
        )
    )

    # Get response after tool execution
    after_tool_result = await client.create(messages=messages)

    # Check we got a text response
    assert isinstance(after_tool_result.content, str)

    # Test multiple tool use
    multi_tool_prompt: List[LLMMessage] = [
        SystemMessage(content="Use the tools as needed to help the user."),
        UserMessage(content="First process the text 'test' and then add 2 and 3.", source="user"),
    ]

    multi_tool_result = await client.create(messages=multi_tool_prompt, tools=[pass_tool, add_tool])

    # We just need to verify we get at least one tool call
    assert isinstance(multi_tool_result.content, list)
    assert len(multi_tool_result.content) > 0
    assert isinstance(multi_tool_result.content[0], FunctionCall)