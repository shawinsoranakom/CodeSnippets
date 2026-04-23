async def _committee_docs_detail_fetch(
    url: str, api_key: str, sem, session=None
) -> dict | None:
    """Fetch a single detail endpoint, respecting a shared semaphore.

    Retries up to 3 times with exponential backoff on rate-limit responses.

    Parameters
    ----------
    url : str
        The detail endpoint URL.
    api_key : str
        The congress.gov API key.
    sem : asyncio.Semaphore
        Shared concurrency limiter.
    session : optional
        Cached aiohttp session.

    Returns
    -------
    dict | None
        The JSON response dict, or None on failure.
    """
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    sep = "&" if "?" in url else "?"
    full_url = f"{url}{sep}format=json&api_key={api_key}"
    kwargs: dict = {}

    if session is not None:
        kwargs["session"] = session

    for attempt in range(4):
        async with sem:
            try:
                resp = await amake_request(full_url, timeout=15, **kwargs)
            except Exception:
                return None

        if not isinstance(resp, dict):
            return None

        if resp.get("error", {}).get("code") == "OVER_RATE_LIMIT":
            if attempt < 3:
                await asyncio.sleep(2**attempt)
                continue

            return None

        return resp

    return None