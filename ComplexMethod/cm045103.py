async def test_anthropic_thinking_mode_streaming() -> None:
    """Test thinking mode with streaming."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        pytest.skip("ANTHROPIC_API_KEY not found in environment variables")

    client = AnthropicChatCompletionClient(
        model="claude-sonnet-4-20250514",  # Use a model that supports thinking
        api_key=api_key,
    )

    messages = [UserMessage(content="What is 15 + 27? Think through it step by step.", source="test")]

    thinking_config = {"thinking": {"type": "enabled", "budget_tokens": 1500}}

    chunks: List[str | CreateResult] = []
    async for chunk in client.create_stream(messages, extra_create_args=thinking_config):
        chunks.append(chunk)

    # Should have received chunks
    assert len(chunks) > 1

    # Final result should have thinking content
    final_result = chunks[-1]
    assert isinstance(final_result, CreateResult)
    assert isinstance(final_result.content, str)
    assert final_result.thought is not None
    assert len(final_result.thought) > 10
    # Should contain the answer
    assert "42" in final_result.content