async def _fetch_meetings_via_listing(
    chamber: str,
    system_code: str,
    parent_code: str,
    congress: int,
    api_key: str,
    sem,
    session=None,
) -> list[dict]:
    """Fetch meeting documents by listing committee-meeting endpoint directly."""
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    kwargs: dict = {}
    if session is not None:
        kwargs["session"] = session

    api_chamber = "nochamber" if chamber.lower() == "joint" else chamber
    url = (
        f"{base_url}committee-meeting/{congress}/{api_chamber}"
        f"?format=json&limit=250&api_key={api_key}"
    )
    all_event_ids: list[str] = []

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

        for m in resp.get("committeeMeetings", []):
            eid = m.get("eventId")
            if eid:
                all_event_ids.append(str(eid))

        next_url = resp.get("pagination", {}).get("next")
        if not next_url:
            break

        url = f"{next_url}&format=json&api_key={api_key}"
        await asyncio.sleep(0.2)

    if not all_event_ids:
        return []

    items: list[dict] = []
    target_codes = {system_code, parent_code}

    async def _process_meeting(eid: str):
        detail_url = (
            f"{base_url}committee-meeting/{congress}/{api_chamber}/{eid}"
            f"?format=json&api_key={api_key}"
        )
        resp = None
        for attempt in range(3):
            async with sem:
                try:
                    resp = await amake_request(detail_url, timeout=20, **kwargs)
                except Exception:
                    return
            if (
                isinstance(resp, dict)
                and resp.get("error", {}).get("code") == "OVER_RATE_LIMIT"
            ):
                await asyncio.sleep(2**attempt)
                continue
            break
        else:
            return

        if not isinstance(resp, dict):
            return

        meeting = resp.get("committeeMeeting", {})
        codes = {c.get("systemCode", "") for c in meeting.get("committees", [])}
        if not codes & target_codes:
            return

        title = meeting.get("title", "")
        raw_date = meeting.get("date", "")
        date_prefix = f"[{raw_date[:10]}] " if raw_date else ""

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
                }
            )

    await asyncio.gather(
        *[_process_meeting(eid) for eid in all_event_ids],
        return_exceptions=True,
    )

    return items