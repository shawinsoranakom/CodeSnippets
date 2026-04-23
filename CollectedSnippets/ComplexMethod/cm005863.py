def test_retry_rollback_uses_retryable_filter():
    """retry_rollback should use is_retryable_create_exception to skip non-retryable errors.

    Validates that the filter correctly identifies non-retryable HTTP status codes
    (via HTTPException, which is checked by is_retryable_create_exception).
    """
    from langflow.services.adapters.deployment.watsonx_orchestrate.core.retry import is_retryable_create_exception

    # Non-retryable status codes should not be retried
    for code in [400, 401, 403, 404, 409, 422]:
        assert not is_retryable_create_exception(HTTPException(status_code=code)), (
            f"HTTPException with status {code} should NOT be retryable"
        )

    # Retryable status codes should be retried
    for code in [500, 502, 503, 504]:
        assert is_retryable_create_exception(HTTPException(status_code=code)), (
            f"HTTPException with status {code} should be retryable"
        )

    # Domain exceptions that are non-retryable
    from lfx.services.adapters.deployment.exceptions import InvalidContentError, ResourceConflictError

    assert not is_retryable_create_exception(ResourceConflictError())
    assert not is_retryable_create_exception(InvalidContentError())

    # Generic exceptions are retryable (e.g. transient network errors)
    assert is_retryable_create_exception(RuntimeError("transient"))