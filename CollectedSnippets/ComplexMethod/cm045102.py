async def test_anthropic_thinking_mode_basic() -> None:
    """Test basic thinking mode functionality."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not found in environment variables")

    client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-20250514",  # Use a model that supports thinking
        api_key=api_key,
        temperature=0.7,  # Should be overridden to 1.0
    )

    messages = [UserMessage(content="Calculate 17 * 23 step by step.", source="test")]

    # Test WITHOUT thinking mode
    result_no_thinking = await client.create(messages)
    assert isinstance(result_no_thinking.content, str)
    assert result_no_thinking.thought is None

    # Test WITH thinking mode
    thinking_config = {"thinking": {"type": "enabled", "budget_tokens": 2000}}

    result_with_thinking = await client.create(messages, extra_create_args=thinking_config)
    assert isinstance(result_with_thinking.content, str)
    # Should have thinking content
    assert result_with_thinking.thought is not None
    assert len(result_with_thinking.thought) > 10
    # Main content should contain the final answer
    assert "391" in result_with_thinking.content or "17" in result_with_thinking.content