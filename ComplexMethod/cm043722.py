async def _process_print(detail_url: str):
        full_url = f"{detail_url}?format=json&api_key={api_key}"

        for attempt in range(3):
            async with sem:
                try:
                    resp = await amake_request(full_url, timeout=20, **kwargs)
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

        for cp in resp.get("committeePrint", []):
            committees = cp.get("committees", [])
            codes = {c.get("systemCode", "") for c in committees}

            if system_code not in codes:
                continue

            title = cp.get("title", "")
            citation = cp.get("citation", "")
            jn = cp.get("jacketNumber")

            if not jn:
                continue

            ch_prefix = {"house": "H", "senate": "S"}.get(chamber.lower(), "J")
            pkg = f"CPRT-{congress}{ch_prefix}PRT{jn}"
            pdf_url = f"https://www.govinfo.gov/content/pkg/{pkg}/pdf/{pkg}.pdf"

            items.append(
                {
                    "doc_type": "publication",
                    "citation": citation or None,
                    "title": title,
                    "congress": congress,
                    "chamber": chamber.title(),
                    "doc_url": pdf_url,
                }
            )