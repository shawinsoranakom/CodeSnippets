def test_tool_retry_initialization_defaults() -> None:
    """Test ToolRetryMiddlewareinitialization with default values."""
    retry = ToolRetryMiddleware()

    assert retry.max_retries == 2
    assert retry._tool_filter is None
    assert retry.tools == []
    assert retry.on_failure == "continue"
    assert retry.backoff_factor == 2.0
    assert retry.initial_delay == 1.0
    assert retry.max_delay == 60.0
    assert retry.jitter is True