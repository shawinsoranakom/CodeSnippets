def scrape_nato() -> set[str]:
    """Scrape NATO member states from Wikipedia."""
    soup = fetch_soup("https://en.wikipedia.org/wiki/Member_states_of_NATO")
    members = set()

    for table in soup.find_all("table", class_="wikitable"):
        prev_header = table.find_previous("h2")
        if not prev_header or "member" not in prev_header.get_text().lower():
            continue
        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if not cells:
                continue
            # First cell with a link is usually the country
            for a in cells[0].find_all("a"):
                code = resolve_country(a.get_text())
                if code:
                    members.add(code)
                    break

    hardcoded = {
        "AL",
        "BE",
        "BG",
        "CA",
        "HR",
        "CZ",
        "DK",
        "EE",
        "FI",
        "FR",
        "DE",
        "GR",
        "HU",
        "IS",
        "IT",
        "LV",
        "LT",
        "LU",
        "ME",
        "NL",
        "MK",
        "NO",
        "PL",
        "PT",
        "RO",
        "SK",
        "SI",
        "ES",
        "SE",
        "TR",
        "GB",
        "US",
    }
    return members if len(members) >= 30 else hardcoded