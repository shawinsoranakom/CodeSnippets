async def _fetch_meetings_via_search(
    chamber: str,
    system_code: str,
    congress: int,
    api_key: str,
    sem,
    session=None,
) -> list[dict]:
    """Fetch meeting/hearing documents using congress.gov search for discovery.

    Step 1: Use search to get the filtered list of event IDs for this committee
            (replaces the broken "list ALL meetings and filter by code" approach).
    Step 2: Skip future-dated events (they have no documents yet).
    Step 3: Fetch API detail for each past event to extract witness/meeting document PDFs.
    Step 4: For past events with no attached PDFs, return the event page URL as fallback.
    """
    # pylint: disable=import-outside-toplevel
    import asyncio
    import re
    from datetime import datetime

    from openbb_congress_gov.utils.congress_search import search_async
    from openbb_core.provider.utils.helpers import amake_request

    committee_name = await _resolve_committee_name(
        chamber, system_code, api_key, session
    )
    if not committee_name:
        return []

    results = await search_async(
        congress=congress,
        sources=["committee-meetings"],
        committee=committee_name,
        chamber=chamber.lower(),  # type: ignore
    )
    if not results:
        return []

    today = datetime.now().date()
    event_pattern = re.compile(r"(?:senate|house|joint)-event/(\d+)")
    event_ids: list[str] = []
    search_meta: dict[str, dict] = {}

    for r in results:
        url = r.get("url", "")
        m = event_pattern.search(url)
        if not m:
            continue

        raw_date = r.get("date", "")
        if raw_date:
            date_part = raw_date.split("\u2014")[0].strip()
            try:
                event_date = datetime.strptime(date_part, "%B %d, %Y").date()
                if event_date > today:
                    continue
            except ValueError:
                pass

        eid = m.group(1)
        if eid not in search_meta:
            event_ids.append(eid)
            search_meta[eid] = r

    if not event_ids:
        return []

    kwargs: dict = {}
    if session is not None:
        kwargs["session"] = session

    api_chamber = "nochamber" if chamber.lower() == "joint" else chamber
    items: list[dict] = []

    async def _process_event(eid: str):
        detail_url = (
            f"{base_url}committee-meeting/{congress}/{api_chamber}/{eid}"
            f"?format=json&api_key={api_key}"
        )
        resp = None
        for attempt in range(4):
            async with sem:
                try:
                    resp = await amake_request(detail_url, timeout=20, **kwargs)
                except Exception:
                    break
            if (
                isinstance(resp, dict)
                and resp.get("error", {}).get("code") == "OVER_RATE_LIMIT"
            ):
                if attempt < 3:
                    await asyncio.sleep(2**attempt)
                    continue
                break
            break

        if not isinstance(resp, dict):
            return

        meeting = resp.get("committeeMeeting", resp)
        title = meeting.get("title", "")
        raw_date = meeting.get("date", "")
        date_prefix = f"[{raw_date[:10]}] " if raw_date else ""

        event_codes = {c.get("systemCode", "") for c in meeting.get("committees", [])}

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

        ch_prefix = {"house": "h", "senate": "s"}.get(chamber.lower(), "j")
        for ht in meeting.get("hearingTranscript", []):
            jn = ht.get("jacketNumber")
            if not jn:
                continue
            pkg = f"CHRG-{congress}{ch_prefix}hrg{jn}"
            pdf_url = f"https://www.govinfo.gov/content/pkg/{pkg}/pdf/{pkg}.pdf"
            label = f"{date_prefix}{title}" if title else f"{date_prefix}Hearing {jn}"
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

    await asyncio.gather(
        *[_process_event(eid) for eid in event_ids],
        return_exceptions=True,
    )

    return items