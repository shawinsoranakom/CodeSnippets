def parse_template_3(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 3, 17: Supply and Distribution by country/year.
    Used for: Cotton Supply, Corn Supply Disappearance

    Single-commodity tables. Countries as section headers, years as rows.
    Attributes are columns (Area Harvested, Production, Imports, etc.)
    """
    report_title = lines[0].strip()
    commodity = extract_commodity_from_title(report_title, commodity_group) or "Unknown"

    # Get column headers from line 2
    header_line = lines[2] if len(lines) > 2 else ""
    columns = [c.strip() for c in header_line.split(",")[1:] if c.strip()]

    unit = extract_unit_from_html(html_text) or "Unknown"  # type: ignore

    data = []
    current_country = None

    for line in lines[3:]:
        line_stripped = line.strip()
        if not line_stripped:
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        has_data = any(parse_value(v) is not None for v in values)

        if first_col and not has_data:
            current_country = first_col
            continue

        if not first_col:
            continue

        year = first_col

        # Determine region/country using helper
        if current_country:
            region_val, country_val = set_region_country(current_country, None)
        else:
            region_val, country_val = None, "Unknown"

        for i, col in enumerate(columns):
            if i < len(values):
                val = parse_value(values[i])
                if val is not None:
                    data.append(
                        {
                            "region": region_val,
                            "country": country_val,
                            "commodity": commodity,
                            "attribute": col,
                            "marketing_year": year,
                            "value": val,
                            "unit": unit,
                        }
                    )

    return {"report": report_title, "template": 3, "row_count": len(data), "data": data}