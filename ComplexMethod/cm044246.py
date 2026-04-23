def build_country_data() -> dict:
    """Build the complete country_data.json structure."""
    # 1. Scrape all group memberships
    group_members: dict[str, set[str]] = {}
    for group_name, scraper in GROUP_SCRAPERS.items():
        print(f"Scraping {group_name}...", end=" ", flush=True)
        try:
            members = scraper()
            group_members[group_name] = members
            print(f"✅ {len(members)} members")
        except Exception as e:
            print(f"❌ Error: {e}")
            group_members[group_name] = set()

    # 2. Sanity checks
    print("\n── Sanity Checks ──")
    for group_name, members in group_members.items():
        expected = EXPECTED_COUNTS.get(group_name)
        count = len(members)
        if expected is None:
            continue
        if isinstance(expected, tuple):
            lo, hi = expected
            ok = lo <= count <= hi
            expected_str = f"{lo}-{hi}"
        elif isinstance(expected, int):
            ok = abs(count - expected) <= 2  # allow ±2 tolerance
            expected_str = str(expected)
        status = "✅" if ok else "⚠️"
        print(f"  {status} {group_name}: got {count}, expected ~{expected_str}")
        if not ok:
            print(f"     Members: {sorted(members)}")

    # 3. Build alpha_2 → groups mapping
    country_groups: dict[str, list[str]] = {}
    for group_name, members in group_members.items():
        for alpha_2 in members:
            country_groups.setdefault(alpha_2, []).append(group_name)

    # Sort group lists for consistency
    for groups in country_groups.values():
        groups.sort()

    # 4. Build country list from pycountry
    countries = []
    for c in sorted(pycountry.countries, key=lambda x: x.alpha_2):  # type: ignore
        entry: dict = {
            "alpha_2": c.alpha_2,  # type: ignore
            "alpha_3": c.alpha_3,  # type: ignore
            "name": _strip_accents(c.name),  # type: ignore
            "numeric": c.numeric,  # type: ignore
        }
        groups = country_groups.get(c.alpha_2)  # type: ignore
        if groups:
            entry["groups"] = groups
        countries.append(entry)

    return {
        "_last_updated": date.today().isoformat(),
        "_sources": {
            "iso_3166": "pycountry library",
            "G7": "https://en.wikipedia.org/wiki/G7",
            "G20": "https://en.wikipedia.org/wiki/G20",
            "EU": "https://european-union.europa.eu/principles-countries-history/eu-countries_en",
            "NATO": "https://en.wikipedia.org/wiki/Member_states_of_NATO",
            "OECD": "https://en.wikipedia.org/wiki/OECD",
            "OPEC": "https://en.wikipedia.org/wiki/OPEC",
            "BRICS": "https://en.wikipedia.org/wiki/BRICS",
        },
        "countries": countries,
    }