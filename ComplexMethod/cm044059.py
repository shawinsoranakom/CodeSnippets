def parse_template_20(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 20: Total Oilseed Area, Yield, and Production.

    Complex structure with country/commodity sections.
    - Aggregate rows (World Total, Total Foreign, Major OilSeeds, Foreign Oilseeds)
    - Regional subtotals (South America, South Asia, etc. with production value on same row)
    - Individual country rows under regions
    """
    # pylint: disable=import-outside-toplevel
    import re

    report_title = lines[0].strip()
    # Extract units from header line
    header_line = lines[3] if len(lines) > 3 else ""
    unit_matches = re.findall(r"\(([^)]+)\)", header_line)
    units = {
        "area": unit_matches[0] if len(unit_matches) > 0 else "Million hectares",
        "yield": (
            unit_matches[1] if len(unit_matches) > 1 else "Metric tons per hectare"
        ),
        "production": (
            unit_matches[2] if len(unit_matches) > 2 else "Million metric tons"
        ),
    }

    # Extract periods from lines 4 and 5
    proj_line = lines[4].split(",") if len(lines) > 4 else []
    period_line = lines[5].split(",") if len(lines) > 5 else []

    periods = []
    current_proj = ""
    for i, p in enumerate(period_line[1:5]):
        _p = p.strip()
        if p:
            proj_val = proj_line[i + 1].strip() if i + 1 < len(proj_line) else ""
            if "Proj" in proj_val:
                current_proj = proj_val.replace(" Proj.", "")

            if current_proj and p in (
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
            "template": 20,
            "row_count": 0,
            "data": [],
            "error": "Could not extract periods from CSV",
        }

    data = []
    current_region = None
    current_commodity = "Total Oilseeds"  # Default commodity for this report

    # Aggregate/commodity names to watch for
    aggregates = ["World Total", "Total Foreign", "Major OilSeeds", "Foreign Oilseeds"]
    special_commodities = ["Oilseed Copra", "Oilseed Palm Kernel"]

    for line in lines[6:]:
        if not line.strip():
            current_region = None
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        if not first_col:
            continue

        values = parts[1:]
        has_data = any(parse_value(v) is not None for v in values)

        if first_col in special_commodities and not has_data:
            current_commodity = first_col
            continue

        # Check if this is a region subtotal line (region name + values on same line)
        region_match = re.match(r"^([A-Za-z ]+)\s+(\d+\.?\d*)$", first_col)

        if not has_data:
            current_region = first_col
            continue

        # Determine entity type and set appropriate values
        is_aggregate = any(agg.lower() in first_col.lower() for agg in aggregates)
        is_special_commodity = first_col in special_commodities

        if region_match:
            # Region subtotal - extract region name
            entity_name = region_match.group(1).strip()
            current_region = entity_name
            commodity = current_commodity
            # Use helper for region/country assignment
            region_val, country_val = set_region_country(entity_name, None)
        elif is_aggregate:
            # Aggregates like "World Total", "Total Foreign"
            commodity = current_commodity
            region_val, country_val = set_region_country(first_col, None)
        elif is_special_commodity:
            commodity = first_col
            region_val, country_val = ("World", "--")
        else:
            # Regular country row
            commodity = current_commodity
            region_val, country_val = set_region_country(first_col, current_region)

        # Emit data for each period and attribute
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

        # Change from last month/year
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

    return {
        "report": report_title,
        "template": 20,
        "row_count": len(data),
        "data": data,
    }