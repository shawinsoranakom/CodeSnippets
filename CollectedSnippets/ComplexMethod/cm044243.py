def scrape_oecd() -> set[str]:
    """Scrape OECD member states from Wikipedia."""
    soup = fetch_soup("https://en.wikipedia.org/wiki/OECD")
    members = set()

    # Find "Member countries" section
    for header in soup.find_all(["h2", "h3"]):
        htext = header.get_text().lower()
        if "member" in htext and "country" in htext or "countries" in htext:
            for sib in header.find_next_siblings():
                if sib.name in ("h2", "h3"):
                    break
                for a in sib.find_all("a"):
                    code = resolve_country(a.get_text())
                    if code:
                        members.add(code)
            break

    hardcoded = {
        "AU",
        "AT",
        "BE",
        "CA",
        "CL",
        "CO",
        "CR",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IS",
        "IE",
        "IL",
        "IT",
        "JP",
        "KR",
        "LV",
        "LT",
        "LU",
        "MX",
        "NL",
        "NZ",
        "NO",
        "PL",
        "PT",
        "SK",
        "SI",
        "ES",
        "SE",
        "CH",
        "TR",
        "GB",
        "US",
    }
    return members if len(members) >= 35 else hardcoded