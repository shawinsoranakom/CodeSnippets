def bitbucket_get(
    client: httpx.Client, url: str, params: dict[str, Any] | None = None
) -> httpx.Response:
    """Perform a GET against Bitbucket with retry and rate limiting.

    Retries on 429 and 5xx responses, and on transport errors. Honors
    `Retry-After` header for 429 when present by sleeping before retrying.
    """
    try:
        response = client.get(url, params=params, timeout=REQUEST_TIMEOUT_SECONDS)
    except httpx.RequestError:
        # Allow retry_builder to handle retries of transport errors
        raise

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        status = e.response.status_code if e.response is not None else None
        if status == 429:
            retry_after = e.response.headers.get("Retry-After") if e.response else None
            if retry_after is not None:
                try:
                    time.sleep(int(retry_after))
                except (TypeError, ValueError):
                    pass
            raise BitbucketRetriableError("Bitbucket rate limit exceeded (429)") from e
        if status is not None and 500 <= status < 600:
            raise BitbucketRetriableError(f"Bitbucket server error: {status}") from e
        if status is not None and 400 <= status < 500:
            raise BitbucketNonRetriableError(f"Bitbucket client error: {status}") from e
        # Unknown status, propagate
        raise

    return response