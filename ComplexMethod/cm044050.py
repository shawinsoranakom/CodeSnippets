def parse_template_1(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 1, 20: Area, Yield, and Production tables.
    Used for: Corn/Cotton/Soybean/Wheat Area Yield Production

    These are single-commodity tables. The commodity is in the title.
    Countries are rows, attributes (area/yield/production) are column groups.
    """
    # pylint: disable=import-outside-toplevel
    import re

    report_title = lines[0].strip()
    commodity = extract_commodity_from_title(report_title, commodity_group) or "Unknown"

    # For Oilseed reports (Template 20), check if it's aggregated
    if "Oilseed" in report_title or "Total" in report_title:
        commodity = "Total Oilseeds"

    # Extract units from header line
    header_line = lines[3] if len(lines) > 3 else ""
    unit_matches = re.findall(r"\(([^)]+)\)", header_line)
    units = {
        "area": unit_matches[0] if len(unit_matches) > 0 else "Unknown",
        "yield": unit_matches[1] if len(unit_matches) > 1 else "Unknown",
        "production": unit_matches[2] if len(unit_matches) > 2 else "Unknown",
    }

    # Extract periods from lines 4 and 5
    proj_line = lines[4].split(",") if len(lines) > 4 else []
    period_line = lines[5].split(",") if len(lines) > 5 else []

    periods = []
    current_proj = ""
    for i, p in enumerate(period_line[1:5]):
        _p = p.strip()
        if _p:
            proj_val = proj_line[i + 1].strip() if i + 1 < len(proj_line) else ""
            if "Proj" in proj_val:
                current_proj = proj_val.replace(" Proj.", "")

            if current_proj and _p in (
                "Jan",
                "Feb",
                "Mar",
                "Apr",
                "May",
                "Jun",
                "Jul",
                "Aug",
                "Sep",
                "Oct",
                "Nov",
                "Dec",
            ):
                periods.append(f"{current_proj} {_p}")
            else:
                periods.append(_p)

    if not periods:
        return {
            "report": report_title,
            "template": 1,
            "row_count": 0,
            "data": [],
            "error": "Could not extract periods from CSV",
        }

    data = []
    current_region = None
    prev_line_empty = False

    for line in lines[6:]:
        if line and not line.strip():
            if prev_line_empty:
                current_region = None
            continue
        if not line:
            prev_line_empty = True
            continue
        prev_line_empty = False

        parts = line.split(",")
        country = parts[0].strip()
        if not country:
            continue

        values = parts[1:]
        has_data = any(parse_value(v) is not None for v in values)

        if not has_data:
            current_region = country
            continue

        # Determine region/country using helper
        region_val, country_val = set_region_country(country, current_region)

        for i, period in enumerate(periods[:4]):
            # Area
            val = parse_value(values[i]) if i < len(values) else None
            if val is not None:
                data.append(
                    {
                        "region": region_val,
                        "country": country_val,
                        "commodity": commodity,
                        "attribute": "Area",
                        "marketing_year": period,
                        "value": val,
                        "unit": units["area"],
                    }
                )

            # Yield
            val = parse_value(values[4 + i]) if 4 + i < len(values) else None
            if val is not None:
                data.append(
                    {
                        "region": region_val,
                        "country": country_val,
                        "commodity": commodity,
                        "attribute": "Yield",
                        "marketing_year": period,
                        "value": val,
                        "unit": units["yield"],
                    }
                )

            # Production
            val = parse_value(values[8 + i]) if 8 + i < len(values) else None
            if val is not None:
                data.append(
                    {
                        "region": region_val,
                        "country": country_val,
                        "commodity": commodity,
                        "attribute": "Production",
                        "marketing_year": period,
                        "value": val,
                        "unit": units["production"],
                    }
                )

        # Change from last month/year (production change for latest projection period)
        latest_period = periods[-1] if periods else "Unknown"
        if len(values) > 12 and parse_value(values[12]) is not None:
            data.append(
                {
                    "region": region_val,
                    "country": country_val,
                    "commodity": commodity,
                    "attribute": "Production Change from Last Month",
                    "marketing_year": latest_period,
                    "value": parse_value(values[12]),
                    "unit": units["production"],
                }
            )
        if len(values) > 13 and parse_value(values[13]) is not None:
            data.append(
                {
                    "region": region_val,
                    "country": country_val,
                    "commodity": commodity,
                    "attribute": "Production Change from Last Month (%)",
                    "marketing_year": latest_period,
                    "value": parse_value(values[13]),
                    "unit": "%",
                }
            )
        if len(values) > 14 and parse_value(values[14]) is not None:
            data.append(
                {
                    "region": region_val,
                    "country": country_val,
                    "commodity": commodity,
                    "attribute": "Production Change from Last Year",
                    "marketing_year": latest_period,
                    "value": parse_value(values[14]),
                    "unit": units["production"],
                }
            )
        if len(values) > 15 and parse_value(values[15]) is not None:
            data.append(
                {
                    "region": region_val,
                    "country": country_val,
                    "commodity": commodity,
                    "attribute": "Production Change from Last Year (%)",
                    "marketing_year": latest_period,
                    "value": parse_value(values[15]),
                    "unit": "%",
                }
            )

    return {"report": report_title, "template": 1, "row_count": len(data), "data": data}