def test_summarization_middleware_find_safe_cutoff_point() -> None:
    """Test `_find_safe_cutoff_point` preserves AI/Tool message pairs."""
    model = FakeToolCallingModel()
    middleware = SummarizationMiddleware(
        model=model, trigger=("messages", 10), keep=("messages", 2)
    )

    messages: list[AnyMessage] = [
        HumanMessage(content="msg1"),
        AIMessage(content="ai", tool_calls=[{"name": "tool", "args": {}, "id": "call1"}]),
        ToolMessage(content="result1", tool_call_id="call1"),
        ToolMessage(content="result2", tool_call_id="call2"),  # orphan - no matching AI
        HumanMessage(content="msg2"),
    ]

    # Starting at a non-ToolMessage returns the same index
    assert middleware._find_safe_cutoff_point(messages, 0) == 0
    assert middleware._find_safe_cutoff_point(messages, 1) == 1

    # Starting at ToolMessage with matching AIMessage moves back to include it
    # ToolMessage at index 2 has tool_call_id="call1" which matches AIMessage at index 1
    assert middleware._find_safe_cutoff_point(messages, 2) == 1

    # Starting at orphan ToolMessage (no matching AIMessage) falls back to advancing
    # ToolMessage at index 3 has tool_call_id="call2" with no matching AIMessage
    # Since we only collect from cutoff_index onwards, only {call2} is collected
    # No match found, so we fall back to advancing past ToolMessages
    assert middleware._find_safe_cutoff_point(messages, 3) == 4

    # Starting at the HumanMessage after tools returns that index
    assert middleware._find_safe_cutoff_point(messages, 4) == 4

    # Starting past the end returns the index unchanged
    assert middleware._find_safe_cutoff_point(messages, 5) == 5

    # Cutoff at or past length stays the same
    assert middleware._find_safe_cutoff_point(messages, len(messages)) == len(messages)
    assert middleware._find_safe_cutoff_point(messages, len(messages) + 5) == len(messages) + 5