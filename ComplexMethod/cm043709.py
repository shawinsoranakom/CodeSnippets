async def _fetch_committee_legislation(
    chamber: str, system_code: str, congress: int, api_key: str, session=None
) -> list[dict]:
    """Fetch legislation PDFs associated with a committee."""
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    _intro_suffix = {
        "hr": "ih",
        "hres": "ih",
        "hjres": "ih",
        "hconres": "ih",
        "s": "is",
        "sres": "is",
        "sjres": "is",
        "sconres": "is",
    }

    kwargs: dict = {}

    if session is not None:
        kwargs["session"] = session

    bills_base = f"{base_url}committee/{chamber}/{system_code}/bills"
    first_url = f"{bills_base}?format=json&limit=250&offset=0&api_key={api_key}"
    resp = await amake_request(first_url, timeout=20, **kwargs)
    all_bills: list[dict] = []

    if isinstance(resp, dict):
        if resp.get("error", {}).get("code") == "OVER_RATE_LIMIT":
            raise OpenBBError(
                ValueError(
                    "Congress.gov API rate limit exceeded. Please wait a moment and try again."
                )
            )

        cb = resp.get("committee-bills", {})
        all_bills = list(cb.get("bills", []) if isinstance(cb, dict) else [])
        total = resp.get("pagination", {}).get("count", 0)

        if total > 250 and all_bills:
            remaining_urls = [
                f"{bills_base}?format=json&limit=250&offset={off}&api_key={api_key}"
                for off in range(250, total, 250)
            ]
            page_sem = asyncio.Semaphore(10)

            async def _fetch_bills_page(page_url: str) -> list[dict]:
                async with page_sem:
                    try:
                        r = await amake_request(page_url, timeout=20, **kwargs)
                    except Exception:
                        return []

                    if not isinstance(r, dict):
                        return []

                    cb2 = r.get("committee-bills", {})

                    return list(cb2.get("bills", []) if isinstance(cb2, dict) else [])

            pages = await asyncio.gather(
                *[_fetch_bills_page(u) for u in remaining_urls]
            )

            for page in pages:
                all_bills.extend(page)

    matched = [b for b in all_bills if b.get("congress") == congress]
    matched = matched[:200]

    items: list[dict] = []

    for b in matched:
        bill_type = b.get("type", "")
        bill_number = b.get("number", "")
        relationship = b.get("relationshipType", "")

        if not bill_type or not bill_number:
            continue

        type_lower = bill_type.lower()
        suffix = _intro_suffix.get(type_lower)

        if not suffix:
            continue

        pdf_url = (
            f"https://www.congress.gov/{congress}/bills/"
            f"{type_lower}{bill_number}/BILLS-{congress}{type_lower}{bill_number}{suffix}.pdf"
        )
        title = b.get("title") or f"{bill_type} {bill_number}"
        citation = f"{bill_type} {bill_number}"

        if relationship:
            title = f"{title} ({relationship})"

        action_date = b.get("actionDate", "")

        if action_date:
            date_str = action_date[:10]
            title = f"[{date_str}] {title}"

        items.append(
            {
                "doc_type": "legislation",
                "citation": citation or None,
                "title": title,
                "congress": congress,
                "chamber": chamber.title(),
                "doc_url": pdf_url,
            }
        )

    return items