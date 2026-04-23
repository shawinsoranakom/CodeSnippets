async def _fetch_hearings_via_api(
    chamber: str,
    system_code: str,
    parent_code: str,
    congress: int,
    api_key: str,
    sem,
    session=None,
) -> list[dict]:
    """Fetch hearing documents for a committee via the hearing API.

    Lists all hearings for the congress/chamber, fetches details concurrently,
    filters by committee systemCode, and extracts PDF URLs + associated meeting docs.
    """
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    kwargs: dict = {}

    if session is not None:
        kwargs["session"] = session

    all_jacket_numbers: list[int] = []
    api_chamber = "nochamber" if chamber.lower() == "joint" else chamber
    url = (
        f"{base_url}hearing/{congress}/{api_chamber}"
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

        for h in resp.get("hearings", []):
            jn = h.get("jacketNumber")

            if jn:
                all_jacket_numbers.append(jn)

        next_url = resp.get("pagination", {}).get("next")

        if not next_url:
            break

        url = f"{next_url}&format=json&api_key={api_key}"
        await asyncio.sleep(0.2)

    items: list[dict] = []
    meeting_event_ids: list[str] = []

    async def _process_hearing(jn: int):
        detail_url = (
            f"{base_url}hearing/{congress}/{api_chamber}/{jn}"
            f"?format=json&api_key={api_key}"
        )

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

        hearing = resp.get("hearing", {})
        committees = hearing.get("committees", [])
        codes = {c.get("systemCode", "") for c in committees}

        if not codes & {system_code, parent_code}:
            return

        title = hearing.get("title", "")
        hearing_dates = hearing.get("dates", [])
        hearing_date = hearing_dates[0].get("date", "") if hearing_dates else ""
        if hearing_date:
            title = f"[{hearing_date}] {title}"

        if system_code in codes:
            pdf_url = ""
            for fmt in hearing.get("formats", []):
                if fmt.get("type") == "PDF":
                    pdf_url = fmt.get("url", "")
                    break
            if not pdf_url:
                ch_prefix = {"house": "h", "senate": "s"}.get(chamber.lower(), "j")
                pkg = f"CHRG-{congress}{ch_prefix}hrg{jn}"
                pdf_url = f"https://www.govinfo.gov/content/pkg/{pkg}/pdf/{pkg}.pdf"
            items.append(
                {
                    "doc_type": "hearing",
                    "citation": hearing.get("citation"),
                    "title": title,
                    "congress": congress,
                    "chamber": chamber.title(),
                    "doc_url": pdf_url,
                    "_committee_codes": codes,
                }
            )

        assoc = hearing.get("associatedMeeting", {})
        event_id = assoc.get("eventId")

        if event_id:
            meeting_event_ids.append(event_id)

    await asyncio.gather(
        *[_process_hearing(jn) for jn in all_jacket_numbers],
        return_exceptions=True,
    )

    if meeting_event_ids:
        meeting_results = await asyncio.gather(
            *[
                _fetch_meeting_documents(congress, chamber, eid, api_key, sem, session)
                for eid in meeting_event_ids
            ],
            return_exceptions=True,
        )

        for result in meeting_results:
            if isinstance(result, list):
                items.extend(result)

    return items