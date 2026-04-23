async def test_anthropic_thinking_mode_with_tools() -> None:
    """Test thinking mode combined with tool calling."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not found in environment variables")

    client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-20250514",  # Use a model that supports thinking
        api_key=api_key,
    )

    # Define tool
    add_tool = FunctionTool(_add_numbers, description="Add two numbers together", name="add_numbers")

    messages = [
        UserMessage(content="I need to add 25 and 17. Use the add tool after thinking about it.", source="test")
    ]

    thinking_config = {"thinking": {"type": "enabled", "budget_tokens": 2000}}

    result = await client.create(messages, tools=[add_tool], extra_create_args=thinking_config)

    # Should get tool calls
    assert isinstance(result.content, list)
    assert len(result.content) >= 1
    assert isinstance(result.content[0], FunctionCall)
    assert result.content[0].name == "add_numbers"

    # Should have thinking content even with tool calls
    assert result.thought is not None
    assert len(result.thought) > 10