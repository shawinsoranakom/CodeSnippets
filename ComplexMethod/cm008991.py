def test_middleware_initialization_validation() -> None:
    """Test that middleware initialization validates parameters correctly."""
    # Test that at least one limit must be specified
    with pytest.raises(ValueError, match="At least one limit must be specified"):
        ModelCallLimitMiddleware()

    # Test invalid exit behavior
    with pytest.raises(ValueError, match="Invalid exit_behavior"):
        ModelCallLimitMiddleware(thread_limit=5, exit_behavior="invalid")  # type: ignore[arg-type]

    # Test valid initialization
    middleware = ModelCallLimitMiddleware(thread_limit=5, run_limit=3)
    assert middleware.thread_limit == 5
    assert middleware.run_limit == 3
    assert middleware.exit_behavior == "end"

    # Test with only thread limit
    middleware = ModelCallLimitMiddleware(thread_limit=5)
    assert middleware.thread_limit == 5
    assert middleware.run_limit is None

    # Test with only run limit
    middleware = ModelCallLimitMiddleware(run_limit=3)
    assert middleware.thread_limit is None
    assert middleware.run_limit == 3