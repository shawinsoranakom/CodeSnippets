def scrape_g7() -> set[str]:
    """Scrape G7 members from Wikipedia.

    G7 membership is extremely stable (no changes since Russia left in 2014),
    so we use the infobox and validate against hardcoded list.
    """
    soup = fetch_soup("https://en.wikipedia.org/wiki/G7")
    hardcoded = {"CA", "FR", "DE", "IT", "JP", "GB", "US"}

    members = set()
    # Look for the infobox — it has a row labeled "Members" with country links
    infobox = soup.find("table", class_="infobox")
    if infobox:
        for tr in infobox.find_all("tr"):
            th = tr.find("th")
            if th and "member" in th.get_text().lower():
                td = tr.find("td")
                if td:
                    for li in td.find_all("li"):
                        a = li.find("a")
                        if a:
                            code = resolve_country(a.get_text())
                            if code:
                                members.add(code)

    return members if 6 <= len(members) <= 9 else hardcoded