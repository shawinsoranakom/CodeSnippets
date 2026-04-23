def test_thread_count_excludes_blocked_run_calls() -> None:
    """Test that thread count only includes allowed calls, not blocked run-scoped calls.

    When run_limit is lower than thread_limit and multiple parallel calls are made,
    only the allowed calls should increment the thread count.

    Example: If run_limit=1 and 3 parallel calls are made, thread count should be 1
    (not 3) because the other 2 were blocked by the run limit.
    """
    # Set run_limit=1, thread_limit=10 (much higher)
    middleware = ToolCallLimitMiddleware(thread_limit=10, run_limit=1, exit_behavior="continue")
    runtime = None

    # Make 3 parallel tool calls - only 1 should be allowed by run_limit
    state = ToolCallLimitState(
        messages=[
            AIMessage(
                "Response",
                tool_calls=[
                    {"name": "search", "args": {}, "id": "1"},
                    {"name": "search", "args": {}, "id": "2"},
                    {"name": "search", "args": {}, "id": "3"},
                ],
            )
        ],
        thread_tool_call_count={},
        run_tool_call_count={},
    )
    result = middleware.after_model(state, runtime)  # type: ignore[arg-type]
    assert result is not None

    # Thread count should be 1 (only the allowed call)
    assert result["thread_tool_call_count"]["__all__"] == 1, (
        "Thread count should only include the 1 allowed call, not the 2 blocked calls"
    )
    # Run count should be 3 (all attempted calls)
    assert result["run_tool_call_count"]["__all__"] == 3, (
        "Run count should include all 3 attempted calls"
    )

    # Verify 2 error messages were created for blocked calls
    assert "messages" in result
    error_messages = [msg for msg in result["messages"] if isinstance(msg, ToolMessage)]
    assert len(error_messages) == 2, "Should have 2 error messages for the 2 blocked calls"