def test_exception_error_message() -> None:
    """Test that the exception provides clear error messages."""
    middleware = ModelCallLimitMiddleware(thread_limit=2, run_limit=1, exit_behavior="error")

    # Test thread limit exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=2, run_model_call_count=0)
    with pytest.raises(ModelCallLimitExceededError) as exc_info:
        middleware.before_model(state, Runtime())

    error_msg = str(exc_info.value)
    assert "Model call limits exceeded" in error_msg
    assert "thread limit (2/2)" in error_msg

    # Test run limit exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=0, run_model_call_count=1)
    with pytest.raises(ModelCallLimitExceededError) as exc_info:
        middleware.before_model(state, Runtime())

    error_msg = str(exc_info.value)
    assert "Model call limits exceeded" in error_msg
    assert "run limit (1/1)" in error_msg

    # Test both limits exceeded
    state = ModelCallLimitState(messages=[], thread_model_call_count=2, run_model_call_count=1)
    with pytest.raises(ModelCallLimitExceededError) as exc_info:
        middleware.before_model(state, Runtime())

    error_msg = str(exc_info.value)
    assert "Model call limits exceeded" in error_msg
    assert "thread limit (2/2)" in error_msg
    assert "run limit (1/1)" in error_msg