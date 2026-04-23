def scrape_brics() -> set[str]:
    """Scrape BRICS member states from Wikipedia."""
    soup = fetch_soup("https://en.wikipedia.org/wiki/BRICS")
    members = set()

    # Find "Member states" section
    for header in soup.find_all(["h2", "h3"]):
        if "member" in header.get_text().lower():
            for sib in header.find_next_siblings():
                if sib.name in ("h2", "h3"):
                    break
                # Look in tables for member states
                if sib.name == "table":
                    for row in sib.find_all("tr"):
                        for a in row.find_all("a"):
                            code = resolve_country(a.get_text())
                            if code:
                                members.add(code)
                for a in sib.find_all("a"):
                    code = resolve_country(a.get_text())
                    if code:
                        members.add(code)
            if members:
                break

    # 2024 expansion: Egypt, Ethiopia, Iran, UAE + Indonesia (Jan 2025)
    hardcoded = {"BR", "RU", "IN", "CN", "ZA", "EG", "ET", "IR", "AE", "ID"}
    return members if len(members) >= 9 else hardcoded