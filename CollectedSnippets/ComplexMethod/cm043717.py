async def fetch_committee_documents(
    chamber: str,
    system_code: str,
    congress: int,
    doc_type: str,
    api_key: str,
    use_cache: bool = True,
) -> list[dict]:
    """Fetch documents for a committee using congress.gov API v3 endpoints.

    Uses:
    - committee/{chamber}/{code}/reports for committee reports
    - hearing/{congress}/{chamber} + detail for hearing PDFs & associated meetings
    - committee-print/{congress}/{chamber} + detail for committee prints
    - committee-meeting detail for witness docs, meeting docs, hearing transcripts
    - committee/{chamber}/{code}/bills for legislation

    All API responses are cached to SQLite (7-day TTL) to avoid redundant requests.
    """
    # pylint: disable=import-outside-toplevel
    import asyncio
    import logging

    from aiohttp_client_cache import SQLiteBackend
    from aiohttp_client_cache.session import CachedSession
    from openbb_core.app.utils import get_user_cache_directory

    logger = logging.getLogger(__name__)
    sem = asyncio.Semaphore(5)
    items: list[dict] = []

    is_subcommittee = len(system_code) > 4 and not system_code.endswith("00")
    parent_code = (
        system_code[: len(system_code) - 2] + "00" if is_subcommittee else system_code
    )
    api_code = parent_code if is_subcommittee else system_code

    if use_cache:
        cache_dir = f"{get_user_cache_directory()}/http/congress_gov"
        backend = SQLiteBackend(cache_dir, expire_after=3600 * 24 * 7)
        _session_ctx = CachedSession(cache=backend)
    else:
        import aiohttp

        _session_ctx = aiohttp.ClientSession()

    async with _session_ctx as session:
        if use_cache:
            await session.delete_expired_responses()  # type: ignore[union-attr]

        tasks = []

        if doc_type in ("all", "report"):
            tasks.append(
                (
                    "report",
                    _fetch_reports_via_api(
                        chamber, api_code, congress, api_key, sem, session
                    ),
                )
            )

        if doc_type in ("all", "hearing", "meeting"):
            tasks.append(
                (
                    "hearing",
                    _fetch_hearings_via_api(
                        chamber,
                        system_code,
                        parent_code,
                        congress,
                        api_key,
                        sem,
                        session,
                    ),
                )
            )

        if doc_type in ("all", "meeting"):
            tasks.append(
                (
                    "meeting",
                    _fetch_meetings_via_search(
                        chamber,
                        system_code,
                        congress,
                        api_key,
                        sem,
                        session,
                    ),
                )
            )

        if doc_type in ("all", "publication"):
            tasks.append(
                (
                    "print",
                    _fetch_prints_via_api(
                        chamber,
                        system_code,
                        congress,
                        api_key,
                        sem,
                        session,
                    ),
                )
            )

        if doc_type in ("all", "legislation"):
            tasks.append(
                (
                    "legislation",
                    _fetch_committee_legislation(
                        chamber, system_code, congress, api_key, session
                    ),
                )
            )

        if tasks:
            results = await asyncio.gather(
                *[t[1] for t in tasks],
                return_exceptions=True,
            )
            for (label, _), result in zip(tasks, results):
                if isinstance(result, list):
                    items.extend(result)
                elif isinstance(result, BaseException):
                    logger.warning("%s pipeline error: %s", label, result)

    seen_urls: set[str] = set()
    deduped: list[dict] = []

    for item in items:
        url = item.get("doc_url", "")

        if url and url not in seen_urls:
            seen_urls.add(url)
            deduped.append(item)

    if is_subcommittee:
        url_code = system_code[2:].upper()
        pattern = f"-{url_code}-"
        filtered: list[dict] = []
        for d in deduped:
            codes = d.get("_committee_codes")
            if codes is not None:
                if system_code in codes:
                    filtered.append(d)
            elif pattern in d.get("doc_url", ""):
                filtered.append(d)
        deduped = filtered

    for d in deduped:
        d.pop("_committee_codes", None)

    return deduped