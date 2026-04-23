def test_middleware_initialization_validation() -> None:
    """Test that middleware initialization validates parameters correctly."""
    # Test that at least one limit must be specified
    with pytest.raises(ValueError, match="At least one limit must be specified"):
        ToolCallLimitMiddleware()

    # Test valid initialization with both limits
    middleware = ToolCallLimitMiddleware(thread_limit=5, run_limit=3)
    assert middleware.thread_limit == 5
    assert middleware.run_limit == 3
    assert middleware.exit_behavior == "continue"
    assert middleware.tool_name is None

    # Test with tool name
    middleware = ToolCallLimitMiddleware(tool_name="search", thread_limit=5)
    assert middleware.tool_name == "search"
    assert middleware.thread_limit == 5
    assert middleware.run_limit is None

    # Test exit behaviors
    for behavior in ["error", "end", "continue"]:
        middleware = ToolCallLimitMiddleware(thread_limit=5, exit_behavior=behavior)
        assert middleware.exit_behavior == behavior

    # Test invalid exit behavior
    with pytest.raises(ValueError, match="Invalid exit_behavior"):
        ToolCallLimitMiddleware(thread_limit=5, exit_behavior="invalid")  # type: ignore[arg-type]

    # Test run_limit exceeding thread_limit
    with pytest.raises(
        ValueError,
        match=r"run_limit .* cannot exceed thread_limit",
    ):
        ToolCallLimitMiddleware(thread_limit=3, run_limit=5)

    # Test run_limit equal to thread_limit (should be valid)
    middleware = ToolCallLimitMiddleware(thread_limit=5, run_limit=5)
    assert middleware.thread_limit == 5
    assert middleware.run_limit == 5

    # Test run_limit less than thread_limit (should be valid)
    middleware = ToolCallLimitMiddleware(thread_limit=5, run_limit=3)
    assert middleware.thread_limit == 5
    assert middleware.run_limit == 3