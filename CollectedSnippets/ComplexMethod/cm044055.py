def parse_template_13(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 13: Multi-commodity supply/demand tables.
    Used for: China Grain Supply, EU Grain Supply

    Structure (from raw CSV):
    - Row 0: Title (e.g., "China: Grain Supply and Demand")
    - Row 3: Attribute headers (Area Harvested, Yield, Production, Imports, etc.)
    - Row 5+: Commodity sections (Wheat, Coarse Grains, etc.) with year rows

    Country is in the title (China, EU, etc.)
    """
    report_title = lines[0].strip()

    # Extract country from title (e.g., "China: Grain Supply" -> "China")
    country = None
    if ":" in report_title:
        country = report_title.split(":")[0].strip()
    else:
        # Try common patterns
        for c in ["China", "EU", "India", "Brazil", "Russia"]:
            if c in report_title:
                country = c
                break

    if not country:
        country = "Unknown"

    # Determine region/country using helper
    region_val, country_val = set_region_country(country, None)

    # Get column headers from line 3
    header_line = lines[3] if len(lines) > 3 else ""
    columns = [c.strip() for c in header_line.split(",")[1:] if c.strip()]

    unit = extract_unit_from_html(html_text) or "Millions of Metric Tons/Hectares"  # type: ignore

    data = []
    current_commodity = None

    for line in lines[4:]:
        if not line.strip():
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        has_data = any(parse_value(v) is not None for v in values)

        # Section header = commodity (Wheat, Coarse Grains, etc.)
        if first_col and not has_data:
            current_commodity = first_col
            continue

        if not first_col:
            continue

        # first_col = marketing year
        year = first_col

        for i, col in enumerate(columns):
            if i < len(values):
                val = parse_value(values[i])
                if val is not None:
                    data.append(
                        {
                            "region": region_val,
                            "country": country_val,
                            "commodity": current_commodity,
                            "attribute": col,
                            "marketing_year": year,
                            "value": val,
                            "unit": unit,
                        }
                    )

    return {
        "report": report_title,
        "template": 13,
        "row_count": len(data),
        "data": data,
    }