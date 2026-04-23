def test_middleware_unit_functionality() -> None:
    """Test that the middleware works as expected in isolation."""
    # Test with end behavior
    middleware = ModelCallLimitMiddleware(thread_limit=2, run_limit=1)

    runtime = Runtime()

    # Test when limits are not exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=0, run_model_call_count=0)
    result = middleware.before_model(state, runtime)
    assert result is None

    # Test when thread limit is exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=2, run_model_call_count=0)
    result = middleware.before_model(state, runtime)
    assert result is not None
    assert result["jump_to"] == "end"
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert "thread limit (2/2)" in result["messages"][0].content

    # Test when run limit is exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=1, run_model_call_count=1)
    result = middleware.before_model(state, runtime)
    assert result is not None
    assert result["jump_to"] == "end"
    assert "messages" in result
    assert len(result["messages"]) == 1
    assert "run limit (1/1)" in result["messages"][0].content

    # Test with error behavior
    middleware_exception = ModelCallLimitMiddleware(
        thread_limit=2, run_limit=1, exit_behavior="error"
    )

    # Test exception when thread limit exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=2, run_model_call_count=0)
    with pytest.raises(ModelCallLimitExceededError) as exc_info:
        middleware_exception.before_model(state, runtime)

    assert "thread limit (2/2)" in str(exc_info.value)

    # Test exception when run limit exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=1, run_model_call_count=1)
    with pytest.raises(ModelCallLimitExceededError) as exc_info:
        middleware_exception.before_model(state, runtime)

    assert "run limit (1/1)" in str(exc_info.value)