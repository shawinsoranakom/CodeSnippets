def test_model_retry_initialization_custom() -> None:
    """Test ModelRetryMiddleware initialization with custom values."""
    retry = ModelRetryMiddleware(
        max_retries=5,
        retry_on=(ValueError, RuntimeError),
        on_failure="error",
        backoff_factor=1.5,
        initial_delay=0.5,
        max_delay=30.0,
        jitter=False,
    )

    assert retry.max_retries == 5
    assert retry.tools == []
    assert retry.retry_on == (ValueError, RuntimeError)
    assert retry.on_failure == "error"
    assert retry.backoff_factor == 1.5
    assert retry.initial_delay == 0.5
    assert retry.max_delay == 30.0
    assert retry.jitter is False