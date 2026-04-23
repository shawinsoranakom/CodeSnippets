def http_status_for_deployment_error(exc: DeploymentServiceError) -> int:
    """Return the HTTP status code that best represents a domain exception.

    This is the inverse of :func:`raise_as_deployment_error`: given a
    domain exception instance, it returns the HTTP status code that an API
    layer should use when surfacing the error to a client.

    Order mirrors the except-chain priority in the Langflow route layer:
    more specific exception types are checked before their parents.
    """
    if isinstance(exc, ResourceConflictError):
        return status.HTTP_409_CONFLICT
    if isinstance(exc, InvalidDeploymentOperationError):
        return status.HTTP_400_BAD_REQUEST
    if isinstance(exc, DeploymentSupportError):
        return status.HTTP_400_BAD_REQUEST
    if isinstance(exc, InvalidDeploymentTypeError):
        return status.HTTP_400_BAD_REQUEST
    if isinstance(exc, InvalidContentError):
        return status.HTTP_422_UNPROCESSABLE_ENTITY
    if isinstance(exc, DeploymentNotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, ResourceNotFoundError):
        return status.HTTP_404_NOT_FOUND
    if isinstance(exc, RateLimitError):
        return status.HTTP_429_TOO_MANY_REQUESTS
    if isinstance(exc, DeploymentTimeoutError):
        return status.HTTP_408_REQUEST_TIMEOUT
    if isinstance(exc, ServiceUnavailableError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if isinstance(exc, OperationNotSupportedError):
        return status.HTTP_501_NOT_IMPLEMENTED
    if isinstance(exc, DeploymentNotConfiguredError):
        return status.HTTP_503_SERVICE_UNAVAILABLE
    if isinstance(exc, AuthenticationError):
        return status.HTTP_401_UNAUTHORIZED
    if isinstance(exc, AuthorizationError):
        return status.HTTP_403_FORBIDDEN
    if isinstance(exc, DeploymentError):
        return status.HTTP_500_INTERNAL_SERVER_ERROR
    return status.HTTP_500_INTERNAL_SERVER_ERROR