def scrape_opec() -> set[str]:
    """Scrape OPEC member states from Wikipedia."""
    soup = fetch_soup("https://en.wikipedia.org/wiki/OPEC")
    members = set()

    # Find "Current members" or "Member countries" section
    for header in soup.find_all(["h2", "h3"]):
        htext = header.get_text().lower()
        if ("current" in htext and "member" in htext) or (
            "member" in htext and ("country" in htext or "countries" in htext)
        ):
            for sib in header.find_next_siblings():
                if sib.name in ("h2", "h3"):
                    break
                for a in sib.find_all("a"):
                    code = resolve_country(a.get_text())
                    if code:
                        members.add(code)
            if members:
                break

    hardcoded = {
        "DZ",
        "CG",
        "GQ",
        "GA",
        "IR",
        "IQ",
        "KW",
        "LY",
        "NG",
        "SA",
        "AE",
        "VE",
    }
    return members if len(members) >= 10 else hardcoded