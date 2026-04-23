def test_summarization_middleware_many_parallel_tool_calls_safety() -> None:
    """Test cutoff safety preserves AI message with many parallel tool calls."""
    middleware = SummarizationMiddleware(
        model=MockChatModel(), trigger=("messages", 15), keep=("messages", 5)
    )
    tool_calls = [{"name": f"tool_{i}", "args": {}, "id": f"call_{i}"} for i in range(10)]
    human_message = HumanMessage(content="calling 10 tools")
    ai_message = AIMessage(content="calling 10 tools", tool_calls=tool_calls)
    tool_messages = [
        ToolMessage(content=f"result_{i}", tool_call_id=f"call_{i}") for i in range(10)
    ]
    messages: list[AnyMessage] = [human_message, ai_message, *tool_messages]

    # Cutoff at index 7 (a ToolMessage) moves back to index 1 (AIMessage)
    # to preserve the AI/Tool pair together
    assert middleware._find_safe_cutoff_point(messages, 7) == 1

    # Any cutoff pointing at a ToolMessage (indices 2-11) moves back to index 1
    for i in range(2, 12):
        assert middleware._find_safe_cutoff_point(messages, i) == 1

    # Cutoff at index 0, 1 (before tool messages) stays the same
    assert middleware._find_safe_cutoff_point(messages, 0) == 0
    assert middleware._find_safe_cutoff_point(messages, 1) == 1