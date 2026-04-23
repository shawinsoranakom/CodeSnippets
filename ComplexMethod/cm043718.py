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