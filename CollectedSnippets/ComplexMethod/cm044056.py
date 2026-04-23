def parse_template_2(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 2: World Crop Production Summary.

    Structure:
    - Row 3: Regions (World, Total Foreign, North America, FSU-12, Asia (WAP), ...)
    - Row 4: Countries under each region
    - Commodity sections (Wheat, Coarse Grains, Rice, etc.) with marketing year rows

    Attribute is ALWAYS "Production" for this template.
    """
    report_title = lines[0].strip()

    # Get region/country headers from lines 3-4
    region_line = lines[3].split(",") if len(lines) > 3 else []
    country_line = lines[4].split(",") if len(lines) > 4 else []

    columns = []
    current_region = None

    for i, region_value in enumerate(region_line):
        region = region_value.strip()
        country = country_line[i].strip() if i < len(country_line) else ""
        country = country.replace("- ", "").replace(" -", "")

        if region:
            current_region = region

        if i == 0:
            continue

        # Use set_region_country for proper region/country assignment
        if current_region and not country:
            # This is a region-level aggregate (World, Total Foreign, North America, etc.)
            region_val, country_val = set_region_country(current_region, None)
            columns.append((region_val, country_val))
        elif country and current_region:
            # This is a country under a region
            # Apply alias normalization to region name
            normalized_region = REGION_ALIASES.get(current_region, current_region)
            columns.append((normalized_region, country))
        elif country:
            # Country without a region
            columns.append((None, country))

    unit_line = lines[5] if len(lines) > 5 else ""
    unit = unit_line.strip().strip("-").strip() or "Million metric tons"

    data = []
    current_commodity = None
    current_proj_year = None

    def looks_like_year(s: str) -> bool:
        """Heuristic to determine if a string looks like a year or projection indicator."""
        s = s.lower().strip()
        return (
            "/" in s
            or "proj" in s
            or "prel" in s
            or s
            in (
                "nov",
                "dec",
                "jan",
                "feb",
                "mar",
                "apr",
                "may",
                "jun",
                "jul",
                "aug",
                "sep",
                "oct",
            )
        )

    for line in lines[6:]:
        if not line.strip():
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        has_data = any(parse_value(v) is not None for v in values)

        if first_col and not has_data:
            if looks_like_year(first_col):
                if "proj" in first_col.lower():
                    current_proj_year = (
                        first_col.replace("proj.", "").replace("Proj.", "").strip()
                    )
                continue
            current_commodity = first_col.strip()
            current_proj_year = None
            continue

        if not first_col and not has_data:
            continue

        if first_col:
            if "proj" in first_col.lower():
                current_proj_year = (
                    first_col.replace("proj.", "").replace("Proj.", "").strip()
                )
                continue
            if first_col.strip() in (
                "Nov",
                "Dec",
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
            ):
                marketing_year = (
                    f"{current_proj_year} {first_col.strip()}"
                    if current_proj_year
                    else first_col.strip()
                )
            else:
                marketing_year = first_col.strip()
                current_proj_year = None
        else:
            continue

        for i, (region, country) in enumerate(columns):
            if i < len(values):
                val = parse_value(values[i])
                if val is not None:
                    data.append(
                        {
                            "region": region,
                            "country": country,
                            "commodity": current_commodity,
                            "attribute": "Production",
                            "marketing_year": marketing_year,
                            "value": val,
                            "unit": unit,
                        }
                    )

    return {"report": report_title, "template": 2, "row_count": len(data), "data": data}