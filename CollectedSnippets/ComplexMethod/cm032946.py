def sync_request(
    method: str,
    url: str,
    *,
    timeout: float | httpx.Timeout | None = None,
    follow_redirects: bool | None = None,
    max_redirects: Optional[int] = None,
    headers: Optional[Dict[str, str]] = None,
    auth_token: Optional[str] = None,
    retries: Optional[int] = None,
    backoff_factor: Optional[float] = None,
    proxy: Any = None,
    **kwargs: Any,
) -> httpx.Response:
    """Synchronous counterpart to async_request, for CLI/tests or sync contexts."""
    timeout = timeout if timeout is not None else DEFAULT_TIMEOUT
    follow_redirects = (
        DEFAULT_FOLLOW_REDIRECTS if follow_redirects is None else follow_redirects
    )
    max_redirects = DEFAULT_MAX_REDIRECTS if max_redirects is None else max_redirects
    retries = DEFAULT_MAX_RETRIES if retries is None else max(retries, 0)
    backoff_factor = (
        DEFAULT_BACKOFF_FACTOR if backoff_factor is None else backoff_factor
    )
    headers = _clean_headers(headers, auth_token=auth_token)
    proxy = DEFAULT_PROXY if proxy is None else proxy

    with httpx.Client(
        timeout=timeout,
        follow_redirects=follow_redirects,
        max_redirects=max_redirects,
        proxy=proxy,
    ) as client:
        last_exc: Exception | None = None
        for attempt in range(retries + 1):
            try:
                start = time.monotonic()
                response = client.request(
                    method=method, url=url, headers=headers, **kwargs
                )
                duration = time.monotonic() - start
                logger.debug(
                    f"sync_request {method} {url} -> {response.status_code} in {duration:.3f}s"
                )
                return response
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt >= retries:
                    logger.warning(
                        f"sync_request exhausted retries for {method} {url}: {exc}"
                    )
                    raise
                delay = _get_delay(backoff_factor, attempt)
                logger.warning(
                    f"sync_request attempt {attempt + 1}/{retries + 1} failed for {method} {url}: {exc}; retrying in {delay:.2f}s"
                )
                time.sleep(delay)
        raise last_exc