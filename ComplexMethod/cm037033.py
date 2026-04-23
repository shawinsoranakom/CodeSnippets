def _is_retryable(exc: Exception) -> bool:
    """Return True for transient errors that are worth retrying.

    Retryable:
      - Timeouts (aiohttp, requests, stdlib)
      - Connection-level failures (refused, reset, DNS)
      - Server errors (5xx) -- includes S3 503 SlowDown
    Not retryable:
      - Client errors (4xx) -- bad URL, auth, not-found
      - Programming errors (ValueError, TypeError, ...)
    """
    # Timeouts
    if isinstance(
        exc,
        (
            TimeoutError,
            asyncio.TimeoutError,
            requests.exceptions.Timeout,
            aiohttp.ServerTimeoutError,
        ),
    ):
        return True
    # Connection-level failures
    if isinstance(
        exc,
        (
            ConnectionError,
            aiohttp.ClientConnectionError,
            requests.exceptions.ConnectionError,
        ),
    ):
        return True
    # aiohttp server-side disconnects
    if isinstance(exc, aiohttp.ServerDisconnectedError):
        return True
    # requests 5xx -- raise_for_status() throws HTTPError
    if (
        isinstance(exc, requests.exceptions.HTTPError)
        and exc.response is not None
        and exc.response.status_code >= 500
    ):
        return True
    # aiohttp 5xx -- raise_for_status() throws ClientResponseError
    return isinstance(exc, aiohttp.ClientResponseError) and exc.status >= 500