def parse_template_5(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 5: World Trade/Production tables - COMMODITY VIEW (Oilseeds).

    Structure (from raw CSV):
    - Attribute (Production, Imports, Exports) is section header
    - Commodity (Oilseed Copra, Oilseed Soybean) is the row identifier
    - Marketing years are columns
    - NO country - this is world-level aggregate data
    """
    report_title = lines[0].strip()

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

        # Section header = attribute (Production, Imports, etc)
        if first_col and not has_data:
            current_attribute = first_col
            continue

        if not first_col:
            continue

        # first_col = commodity name (Oilseed Copra, etc)
        commodity = first_col

        for i, period in enumerate(periods):
            if i < len(values):
                val = parse_value(values[i])
                if val is not None:
                    data.append(
                        {
                            "region": "World",
                            "country": "--",  # World aggregates
                            "commodity": commodity,
                            "attribute": current_attribute,
                            "marketing_year": period,
                            "value": val,
                            "unit": unit,
                        }
                    )

    return {"report": report_title, "template": 5, "row_count": len(data), "data": data}