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