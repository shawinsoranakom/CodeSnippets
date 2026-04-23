async def test_openai_tool_choice_auto_integration() -> None:
    """Test tool_choice parameter with 'auto' setting using the actual OpenAI API."""
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

    # Test auto tool choice - model should choose to use add_numbers for math
    result = await client.create(
        messages=[UserMessage(content="What is 15 plus 27?", source="user")],
        tools=[pass_tool, add_tool],
        tool_choice="auto",  # Let model choose
    )

    assert isinstance(result.content, list)
    assert len(result.content) == 1
    assert isinstance(result.content[0], FunctionCall)
    assert result.content[0].name == "_add_numbers"
    assert result.finish_reason == "function_calls"
    assert result.usage is not None

    # Parse arguments to verify correct values
    args = json.loads(result.content[0].arguments)
    assert args["a"] == 15
    assert args["b"] == 27