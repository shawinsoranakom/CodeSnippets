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