def raise_as_deployment_error(
    *,
    status_code: int | None,
    detail: str,
    message_prefix: str | None = None,
    resource: str | None = None,
    resource_name: str | None = None,
    cause: Exception | None = None,
) -> NoReturn:
    """Raise domain-specific deployment exceptions based on HTTP-like status/detail.

    When *cause* is ``None`` (the default), implicit exception chaining is
    suppressed (``raise … from None``).  Pass the original exception as
    *cause* to preserve the traceback chain for debugging.  Callers that
    handle security-sensitive errors (e.g. credential verification) should
    set it to None to avoid leaking provider responses through the exception chain.

    For conflict errors, callers should pass ``resource`` and ``resource_name``
    whenever known. This helper does not infer conflict hints from free-form
    provider detail text.
    """
    detail_text = str(detail)
    detail_lower = detail_text.lower()
    prefix = str(message_prefix or "").strip()
    message = f"{prefix} error details: {detail_text}" if prefix else detail_text

    if status_code == status.HTTP_401_UNAUTHORIZED:
        raise AuthenticationError(message=message, error_code="authentication_error", cause=cause) from cause
    if status_code == status.HTTP_403_FORBIDDEN:
        raise AuthorizationError(message=message, error_code="authorization_error", cause=cause) from cause
    if status_code == status.HTTP_422_UNPROCESSABLE_CONTENT:
        raise InvalidContentError(message=message, cause=cause) from cause
    if status_code == status.HTTP_400_BAD_REQUEST:
        raise InvalidDeploymentOperationError(message=message, cause=cause) from cause
    if status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
        raise InvalidDeploymentOperationError(message=message, cause=cause) from cause
    if status_code == status.HTTP_413_REQUEST_ENTITY_TOO_LARGE:
        raise InvalidContentError(message=message, cause=cause) from cause
    if status_code == status.HTTP_415_UNSUPPORTED_MEDIA_TYPE:
        raise InvalidContentError(message=message, cause=cause) from cause
    if status_code == status.HTTP_404_NOT_FOUND:
        raise ResourceNotFoundError(message, cause=cause) from cause
    if status_code == status.HTTP_410_GONE:
        raise ResourceNotFoundError(message, cause=cause) from cause
    if status_code == status.HTTP_409_CONFLICT:
        raise ResourceConflictError(
            message=message,
            resource=resource,
            resource_name=resource_name,
            cause=cause,
        ) from cause
    if status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        raise RateLimitError(message=message, cause=cause) from cause
    if status_code in {status.HTTP_408_REQUEST_TIMEOUT, status.HTTP_504_GATEWAY_TIMEOUT}:
        raise DeploymentTimeoutError(message=message, cause=cause) from cause
    if status_code in {status.HTTP_502_BAD_GATEWAY, status.HTTP_503_SERVICE_UNAVAILABLE}:
        raise ServiceUnavailableError(message=message, cause=cause) from cause
    if "not found" in detail_lower:
        raise ResourceNotFoundError(message, cause=cause) from cause
    if "already exists" in detail_lower or "conflict" in detail_lower:
        raise ResourceConflictError(
            message=message,
            resource=resource,
            resource_name=resource_name,
            cause=cause,
        ) from cause
    if "unprocessable" in detail_lower:
        raise InvalidContentError(message=message, cause=cause) from cause
    if "too many requests" in detail_lower or "rate limit" in detail_lower:
        raise RateLimitError(message=message, cause=cause) from cause
    if "timed out" in detail_lower or "timeout" in detail_lower:
        raise DeploymentTimeoutError(message=message, cause=cause) from cause
    if (
        "service unavailable" in detail_lower
        or "temporarily unavailable" in detail_lower
        or "bad gateway" in detail_lower
    ):
        raise ServiceUnavailableError(message=message, cause=cause) from cause
    if "unauthorized" in detail_lower or "authentication" in detail_lower:
        raise AuthenticationError(message=message, error_code="authentication_error", cause=cause) from cause
    if "forbidden" in detail_lower or "permission" in detail_lower or "not allowed" in detail_lower:
        raise AuthorizationError(message=message, error_code="authorization_error", cause=cause) from cause
    if "bad request" in detail_lower:
        raise InvalidDeploymentOperationError(message=message, cause=cause) from cause
    if (
        "invalid" in detail_lower
        or "missing" in detail_lower
        or "required" in detail_lower
        or "malformed" in detail_lower
    ):
        raise InvalidContentError(message=message, cause=cause) from cause
    raise DeploymentError(message=message, error_code="deployment_error", cause=cause) from cause