def scrape_g20() -> set[str]:
    """Scrape G20 members from Wikipedia."""
    soup = fetch_soup("https://en.wikipedia.org/wiki/G20")
    hardcoded = {
        "AR",
        "AU",
        "BR",
        "CA",
        "CN",
        "FR",
        "DE",
        "IN",
        "ID",
        "IT",
        "JP",
        "KR",
        "MX",
        "RU",
        "SA",
        "ZA",
        "TR",
        "GB",
        "US",
    }

    members = set()
    # Find the member states section
    for header in soup.find_all(["h2", "h3"]):
        if "member" in header.get_text().lower():
            # Scan the next sibling elements for a table or list
            for sib in header.find_next_siblings():
                if sib.name in ("h2", "h3"):
                    break
                for a in sib.find_all("a"):
                    code = resolve_country(a.get_text())
                    if code:
                        members.add(code)

    # Filter to reasonable count (G20 has 19 country members + EU)
    return members if len(members) >= 19 else hardcoded