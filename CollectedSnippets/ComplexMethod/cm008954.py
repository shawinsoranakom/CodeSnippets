def test_middleware_unit_functionality() -> None:
    """Test that the middleware works as expected in isolation.

    Tests basic count tracking, thread limit, run limit, and limit-not-exceeded cases.
    """
    middleware = ToolCallLimitMiddleware(thread_limit=3, run_limit=2, exit_behavior="end")
    runtime = None

    # Test when limits are not exceeded - counts should increment normally
    state = ToolCallLimitState(
        messages=[
            HumanMessage("Question"),
            AIMessage("Response", tool_calls=[{"name": "search", "args": {}, "id": "1"}]),
        ],
        thread_tool_call_count={},
        run_tool_call_count={},
    )
    result = middleware.after_model(state, runtime)  # type: ignore[arg-type]
    assert result is not None
    assert result["thread_tool_call_count"] == {"__all__": 1}
    assert result["run_tool_call_count"] == {"__all__": 1}
    assert "jump_to" not in result

    # Test thread limit exceeded (start at thread_limit so next call will exceed)
    state = ToolCallLimitState(
        messages=[
            HumanMessage("Question 2"),
            AIMessage("Response 2", tool_calls=[{"name": "search", "args": {}, "id": "3"}]),
        ],
        thread_tool_call_count={"__all__": 3},  # Already exceeds thread_limit=3
        run_tool_call_count={"__all__": 0},  # No calls yet
    )
    result = middleware.after_model(state, runtime)  # type: ignore[arg-type]
    assert result is not None
    assert result["jump_to"] == "end"
    # Check the ToolMessage (sent to model - no thread/run details)
    tool_msg = result["messages"][0]
    assert isinstance(tool_msg, ToolMessage)
    assert tool_msg.status == "error"
    assert "Tool call limit exceeded" in tool_msg.content
    # Should include "Do not" instruction
    assert "Do not" in tool_msg.content, (
        "Tool message should include 'Do not' instruction when limit exceeded"
    )
    # Check the final AI message (displayed to user - includes thread/run details)
    final_ai_msg = result["messages"][-1]
    assert isinstance(final_ai_msg, AIMessage)
    assert isinstance(final_ai_msg.content, str)
    assert "limit" in final_ai_msg.content.lower()
    assert "thread limit exceeded" in final_ai_msg.content.lower()
    # Thread count stays at 3 (blocked call not counted)
    assert result["thread_tool_call_count"] == {"__all__": 3}
    # Run count goes to 1 (includes blocked call)
    assert result["run_tool_call_count"] == {"__all__": 1}

    # Test run limit exceeded (thread count must be >= run count)
    state = ToolCallLimitState(
        messages=[
            HumanMessage("Question"),
            AIMessage("Response", tool_calls=[{"name": "search", "args": {}, "id": "1"}]),
        ],
        thread_tool_call_count={"__all__": 2},
        run_tool_call_count={"__all__": 2},
    )
    result = middleware.after_model(state, runtime)  # type: ignore[arg-type]
    assert result is not None
    assert result["jump_to"] == "end"
    # Check the final AI message includes run limit details
    final_ai_msg = result["messages"][-1]
    assert "run limit exceeded" in final_ai_msg.content
    assert "3/2 calls" in final_ai_msg.content
    # Check the tool message (sent to model) - should always include "Do not" instruction
    tool_msg = result["messages"][0]
    assert isinstance(tool_msg, ToolMessage)
    assert "Tool call limit exceeded" in tool_msg.content
    assert "Do not" in tool_msg.content, (
        "Tool message should include 'Do not' instruction for both run and thread limits"
    )