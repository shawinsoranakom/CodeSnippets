async def _fetch_meeting_documents(
    congress: int, chamber: str, event_id: str, api_key: str, sem, session=None
) -> list[dict]:
    """Fetch all documents for a committee meeting."""
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    kwargs: dict = {}

    if session is not None:
        kwargs["session"] = session

    url = (
        f"{base_url}committee-meeting/{congress}"
        f"/{'nochamber' if chamber.lower() == 'joint' else chamber}/{event_id}"
        f"?format=json&api_key={api_key}"
    )
    resp = None

    for attempt in range(4):
        async with sem:
            try:
                resp = await amake_request(url, timeout=20, **kwargs)
            except Exception:
                return []

        if (
            isinstance(resp, dict)
            and resp.get("error", {}).get("code") == "OVER_RATE_LIMIT"
        ):
            if attempt < 3:
                await asyncio.sleep(2**attempt)
                continue

            return []

        break

    if not isinstance(resp, dict):
        return []

    meeting = resp.get("committeeMeeting", resp)
    title = meeting.get("title", "")
    raw_date = meeting.get("date", "")
    date_prefix = f"[{raw_date[:10]}] " if raw_date else ""
    event_codes = {c.get("systemCode", "") for c in meeting.get("committees", [])}
    items: list[dict] = []

    for wd in meeting.get("witnessDocuments", []):
        pdf_url = wd.get("url", "")

        if not pdf_url or wd.get("format") != "PDF":
            continue

        witness = _witness_label(pdf_url)
        label = (
            f"{date_prefix}{witness} \u2014 {title}"
            if title
            else f"{date_prefix}{witness}"
        )
        items.append(
            {
                "doc_type": "meeting",
                "citation": None,
                "title": label,
                "congress": congress,
                "chamber": chamber.title(),
                "doc_url": pdf_url,
                "_committee_codes": event_codes,
            }
        )

    for md in meeting.get("meetingDocuments", []):
        pdf_url = md.get("url", "")

        if not pdf_url or md.get("format") != "PDF":
            continue

        doc_name = md.get("name") or md.get("documentType", "")
        label = (
            f"{date_prefix}{doc_name} \u2014 {title}"
            if doc_name
            else f"{date_prefix}{title}"
        )
        items.append(
            {
                "doc_type": "meeting",
                "citation": None,
                "title": label,
                "congress": congress,
                "chamber": chamber.title(),
                "doc_url": pdf_url,
                "_committee_codes": event_codes,
            }
        )

    return items