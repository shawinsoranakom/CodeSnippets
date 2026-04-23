def parse_template_11(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 11: All Grain Summary Comparison.

    Structure (from raw CSV):
    - Row 3: Commodities (Wheat, Rice Milled, Corn, ...)
    - Row 4: Marketing years repeated for each commodity
    - Attribute (Production, Domestic Consumption, etc.) is section header
    - Country (United States, Other, World Total) is row identifier
    """
    report_title = lines[0].strip()

    # Get commodity headers from line 3
    commodity_line = lines[3].split(",") if len(lines) > 3 else []
    commodities = [c.strip() for c in commodity_line if c.strip()]

    # Get periods from line 4 - they repeat for each commodity
    period_line = lines[4].split(",") if len(lines) > 4 else []
    periods = []
    for p in period_line[2:5]:  # First 3 periods for first commodity
        _p = p.strip()
        if _p:
            periods.append(_p)

    unit = extract_unit_from_html(html_text) or "Million Metric Tons"  # type: ignore

    data = []
    current_attribute = None

    for line in lines[5:]:
        if not line.strip():
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        has_data = any(parse_value(v) is not None for v in values)

        # Section header = attribute
        if first_col and not has_data:
            current_attribute = first_col
            continue

        if not first_col:
            continue

        country = first_col

        # Determine region/country using helper
        region_val, country_val = set_region_country(country, None)

        # Values are: [note], [c1_y1, c1_y2, c1_y3], [c2_y1, c2_y2, c2_y3], ...
        # Skip the note column (values[0])
        val_idx = 1
        for commodity in commodities:
            for period in periods:
                if val_idx < len(values):
                    val = parse_value(values[val_idx])
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
                    val_idx += 1

    return {
        "report": report_title,
        "template": 11,
        "row_count": len(data),
        "data": data,
    }