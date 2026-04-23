async def test_openai_tool_choice_specific_tool_integration() -> None:
    """Test tool_choice parameter with a specific tool using the actual OpenAI API."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not found in environment variables")

    def _pass_function(input: str) -> str:
        """Simple passthrough function."""
        return f"Processed: {input}"

    def _add_numbers(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    model = "gpt-4o-mini"
    client = OpenAIChatCompletionClient(model=model, api_key=api_key)

    # Define tools
    pass_tool = FunctionTool(_pass_function, description="Process input text", name="_pass_function")
    add_tool = FunctionTool(_add_numbers, description="Add two numbers together", name="_add_numbers")

    # Test forcing use of specific tool
    result = await client.create(
        messages=[UserMessage(content="Process the word 'hello'", source="user")],
        tools=[pass_tool, add_tool],
        tool_choice=pass_tool,  # Force use of specific tool
    )

    assert isinstance(result.content, list)
    assert len(result.content) == 1
    assert isinstance(result.content[0], FunctionCall)
    assert result.content[0].name == "_pass_function"
    assert result.finish_reason == "function_calls"
    assert result.usage is not None