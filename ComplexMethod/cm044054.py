def parse_template_8(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 8: Summary tables (like Coffee, Cotton World Supply).
    Attribute = section header, Country = row, periods = columns
    """
    report_title = lines[0].strip()
    commodity = extract_commodity_from_title(report_title) or "Unknown"

    # Get periods from line 3
    period_line = lines[3] if len(lines) > 3 else ""
    periods = [p.strip() for p in period_line.split(",")[1:] if p.strip()]

    unit = extract_unit_from_html(html_text) or "Unknown"  # type: ignore

    data = []
    current_attribute = None

    for line in lines[4:]:
        if not line.strip():
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        if first_col.lower() in ("nr", "") and all(
            v.strip().lower() in ("nr", "") for v in values
        ):
            continue

        has_data = any(parse_value(v) is not None for v in values)

        if first_col and not has_data:
            current_attribute = first_col
            continue

        if not first_col:
            continue

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

    return {"report": report_title, "template": 8, "row_count": len(data), "data": data}