def process_mic_data(rows: list[dict], operating_only: bool = False) -> list[dict]:
    """Filter and transform MIC rows into exchange entries."""
    # Normalize header keys (strip whitespace, uppercase)
    active = [r for r in rows if r.get("STATUS", "").strip().upper() == "ACTIVE"]
    logger.info("Active entries: %d", len(active))

    if operating_only:
        active = [
            r for r in active if r.get("OPRT/SGMT", "").strip().upper() in ("OPRT", "O")
        ]
        logger.info("Operating MICs only: %d", len(active))

    exchanges = []
    for row in active:
        mic = row.get("MIC", "").strip()
        if not mic:
            continue

        name = row.get("MARKET NAME-INSTITUTION DESCRIPTION", "").strip()
        if not name:
            continue

        acronym = row.get("ACRONYM", "").strip() or mic

        entry = {
            "mic": mic,
            "acronym": acronym,
            "name": name,
        }

        city = row.get("CITY", "").strip()
        if city:
            entry["city"] = city.title()

        country_code = row.get("ISO COUNTRY CODE (ISO 3166)", "").strip().upper()
        if country_code:
            entry["country"] = country_code

        website = row.get("WEBSITE", "").strip()
        if website:
            # Normalize: ensure lowercase, add https:// if missing scheme
            website = website.lower()
            if website and not website.startswith(("http://", "https://")):
                website = f"https://{website}"
            entry["website"] = website

        entry["_type"] = row.get("OPRT/SGMT", "").strip().upper()
        exchanges.append(entry)

    # Sort operating MICs before segments so that the lookup in exchange_utils
    # (first-write-wins) gives priority to operating MICs when acronyms collide.
    exchanges.sort(key=lambda x: (0 if x["_type"] in ("OPRT", "O") else 1, x["mic"]))

    # Strip internal sort key before output
    for e in exchanges:
        del e["_type"]
    return exchanges