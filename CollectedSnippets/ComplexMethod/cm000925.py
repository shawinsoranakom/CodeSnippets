async def _fetch_generation_cost(
    client: httpx.AsyncClient,
    gen_id: str,
    api_key: str,
    log_prefix: str,
) -> float | None:
    """Fetch the ``total_cost`` for one generation, with retries.

    Retries only on transient conditions:

    * HTTP 404 — row not yet indexed server-side (typical ~5-10s lag
      after the SSE stream closes)
    * HTTP 408 / 429 — timeout / rate limit
    * HTTP 5xx — transient OpenRouter outage
    * Network / ``httpx`` exceptions — transport-level retryable

    Fails fast on permanent client errors (401 Unauthorized,
    403 Forbidden, 400 Bad Request, etc.) since they can't recover
    within the retry window and would just burn API quota.

    Returns ``None`` when the endpoint reports no data, on a permanent
    failure, or when every retry attempt hits a transient error.
    """
    headers = {"Authorization": f"Bearer {api_key}"}
    params = {"id": gen_id}
    last_error: Exception | None = None
    for attempt in range(_MAX_RETRIES):
        if attempt > 0:
            await asyncio.sleep(_BACKOFF_SECONDS[attempt - 1])
        try:
            resp = await client.get(
                _GENERATION_URL,
                params=params,
                headers=headers,
                timeout=_REQUEST_TIMEOUT,
            )
            status = resp.status_code
            # Fast-fail on permanent client errors — retrying 401/403/400
            # just burns API quota and delays the fallback.
            if status in (400, 401, 403):
                logger.warning(
                    "%s OpenRouter /generation permanent error %d for %s — "
                    "not retrying (check API key / request shape)",
                    log_prefix,
                    status,
                    gen_id,
                )
                return None
            # Transient retryable: 404 (indexing lag), 408 (timeout),
            # 429 (rate limit), 5xx (server error).
            if status == 404 or status == 408 or status == 429 or status >= 500:
                last_error = RuntimeError(f"HTTP {status} on attempt {attempt + 1}")
                continue
            # Any other 4xx — treat as permanent.
            if status >= 400:
                logger.warning(
                    "%s OpenRouter /generation unexpected status %d for %s — "
                    "not retrying",
                    log_prefix,
                    status,
                    gen_id,
                )
                return None
            payload = resp.json().get("data")
            if not isinstance(payload, dict):
                logger.warning(
                    "%s OpenRouter /generation returned no data for %s",
                    log_prefix,
                    gen_id,
                )
                return None
            cost = payload.get("total_cost")
            if cost is None:
                logger.warning(
                    "%s OpenRouter /generation response missing total_cost "
                    "for %s (keys=%s)",
                    log_prefix,
                    gen_id,
                    sorted(payload.keys())[:10],
                )
                return None
            return float(cost)
        except Exception as exc:  # noqa: BLE001
            # Network / transport errors are retryable.
            last_error = exc
            continue
    logger.warning(
        "%s OpenRouter /generation lookup failed for %s after %d attempts: %s",
        log_prefix,
        gen_id,
        _MAX_RETRIES,
        last_error,
    )
    return None