def parse_template_7(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 7: Production/Consumption summary - COUNTRY VIEW (Dairy).

    Structure (from raw CSV):
    - Attribute (Production, Domestic Consumption) is section header
    - Country (India, EU, US, etc.) is the row identifier
    - Commodity (Butter, Cheese, etc.) is in the TITLE
    - Marketing years are columns
    """
    report_title = lines[0].strip()

    # Extract commodity from title - e.g. "Butter Production and Consumption"
    # Try to find commodity name at the start of title
    commodity = None
    dairy_commodities = [
        "Butter",
        "Cheese",
        "Milk",
        "Skim Milk Powder",
        "Whole Milk Powder",
        "Whey",
        "Nonfat Dry Milk",
        "Fluid Milk",
    ]
    for dc in dairy_commodities:
        if dc.lower() in report_title.lower():
            commodity = dc
            break

    if not commodity:
        commodity = (
            extract_commodity_from_title(report_title, commodity_group) or "Unknown"
        )

    # Get periods from line 2
    period_line = lines[2] if len(lines) > 2 else ""
    periods = [p.strip() for p in period_line.split(",")[1:] if p.strip()]

    unit = extract_unit_from_html(html_text) or "Unknown"  # type: ignore

    data = []
    current_attribute = None

    for line in lines[3:]:
        if not line.strip():
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        has_data = any(parse_value(v) is not None for v in values)

        # Section header = attribute (Production, Domestic Consumption, etc)
        if first_col and not has_data:
            current_attribute = first_col
            continue

        if not first_col:
            continue

        # first_col = country name (India, EU, etc)
        country = first_col

        # Determine region/country using helper
        region_val, country_val = set_region_country(country, None)

        for i, period in enumerate(periods):
            if i < len(values):
                val = parse_value(values[i])
                if val is not None:
                    data.append(
                        {
                            "region": region_val,
                            "country": country_val,
                            "commodity": commodity,
                            "attribute": current_attribute,
                            "marketing_year": period,
                            "value": val,
                            "unit": unit,
                        }
                    )

    return {"report": report_title, "template": 7, "row_count": len(data), "data": data}