async def _fetch_prints_via_api(
    chamber: str,
    system_code: str,
    congress: int,
    api_key: str,
    sem,
    session=None,
) -> list[dict]:
    """Fetch committee prints filtered by committee systemCode."""
    # pylint: disable=import-outside-toplevel
    import asyncio

    from openbb_core.provider.utils.helpers import amake_request

    kwargs: dict = {}

    if session is not None:
        kwargs["session"] = session

    all_print_urls: list[str] = []
    url = (
        f"{base_url}committee-print/{congress}/{chamber}"
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

        for p in resp.get("committeePrints", []):
            detail_url = p.get("url")

            if detail_url:
                all_print_urls.append(detail_url)

        next_url = resp.get("pagination", {}).get("next")

        if not next_url:
            break

        url = f"{next_url}&format=json&api_key={api_key}"
        await asyncio.sleep(0.2)

    items: list[dict] = []

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

    await asyncio.gather(
        *[_process_print(u) for u in all_print_urls],
        return_exceptions=True,
    )

    return items