async def _fetch_reports_via_api(
    chamber: str, system_code: str, congress: int, api_key: str, sem, session=None
) -> list[dict]:
    """Fetch reports for a committee via the committee-specific reports endpoint."""
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    kwargs: dict = {}

    if session is not None:
        kwargs["session"] = session

    matched: list[dict] = []
    url = (
        f"{base_url}committee/{chamber}/{system_code}/reports"
        f"?format=json&limit=250&api_key={api_key}"
    )

    while url:
        async with sem:
            try:
                resp = await amake_request(url, timeout=20, **kwargs)
            except Exception:
                break

        if not isinstance(resp, dict):
            break

        if resp.get("error", {}).get("code") == "OVER_RATE_LIMIT":
            await asyncio.sleep(2)
            continue

        for rpt in resp.get("reports", []):
            if rpt.get("congress") != congress:
                continue

            matched.append(rpt)

        next_url = resp.get("pagination", {}).get("next")

        if not next_url:
            break

        has_target = False

        for rpt in resp.get("reports", []):
            if rpt.get("congress", 0) <= congress:
                has_target = True
                break

        if not has_target:
            break

        url = f"{next_url}&format=json&api_key={api_key}"
        await asyncio.sleep(0.2)

    if not matched:
        return []

    async def _fetch_report_detail(rpt: dict) -> dict | None:
        citation = rpt.get("citation", "")
        rpt_type = rpt.get("type", "")
        number = rpt.get("number")
        part = rpt.get("part", 1)

        if not number or not rpt_type:
            return None

        type_lower = rpt_type.lower()
        base = f"CRPT-{congress}{type_lower}{number}"

        if ",Part" in citation:
            pdf_url = f"https://www.congress.gov/{congress}/crpt/{type_lower}{number}/{base}-pt{part}.pdf"
        else:
            pdf_url = f"https://www.congress.gov/{congress}/crpt/{type_lower}{number}/{base}.pdf"

        detail_url = (
            f"{base_url}committee-report/{congress}/{rpt_type}/{number}"
            f"?format=json&api_key={api_key}"
        )
        title = citation
        issue_date = ""

        async with sem:
            try:
                detail = await amake_request(detail_url, timeout=20, **kwargs)
            except Exception:
                detail = None

        if isinstance(detail, dict):
            for cr in detail.get("committeeReports", []):
                title = cr.get("title") or citation
                issue_date = (cr.get("issueDate") or "")[:10]
                break

        if issue_date:
            title = f"[{issue_date}] {title}"

        return {
            "doc_type": "report",
            "citation": citation or None,
            "title": title,
            "congress": congress,
            "chamber": chamber.title(),
            "doc_url": pdf_url,
        }

    results = await asyncio.gather(
        *[_fetch_report_detail(r) for r in matched],
        return_exceptions=True,
    )

    return [r for r in results if isinstance(r, dict)]