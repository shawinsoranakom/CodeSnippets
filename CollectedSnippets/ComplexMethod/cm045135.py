async def test_openai_tool_choice_required_integration() -> None:
    """Test tool_choice parameter with 'required' setting using the actual OpenAI API."""
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

    # Test required tool choice - model must use a tool even for general conversation
    result = await client.create(
        messages=[UserMessage(content="Say hello to me", source="user")],
        tools=[pass_tool, add_tool],
        tool_choice="required",  # Force tool usage
    )

    assert isinstance(result.content, list)
    assert len(result.content) == 1
    assert isinstance(result.content[0], FunctionCall)
    assert result.content[0].name in ["_pass_function", "_add_numbers"]
    assert result.finish_reason == "function_calls"
    assert result.usage is not None