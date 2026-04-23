def parse_template_9(
    lines: list, html_text: str | None = None, commodity_group: str | None = None
) -> dict:
    """
    Template 9: Copra, Palm Kernel, Palm Oil Production.

    Multi-commodity table with country rows.
    Commodity is section header, Country is row, periods are columns.
    """
    # pylint: disable=import-outside-toplevel
    import re

    report_title = lines[0].strip()
    unit = extract_unit_from_html(html_text) or "Million metric tons"  # type: ignore

    # Extract periods from line 5 (e.g., "2023/24444" -> "2023/24")
    def clean_period(p):
        """Remove trailing garbage digits from period strings like '2023/24444' -> '2023/24'"""
        p = p.strip()
        if not p:
            return p
        # Match patterns like 2023/24, 2024/25, Nov, Dec, Prel., Proj.
        # Strip any trailing digits that don't belong

        # Handle "2023/24444" -> "2023/24"
        m = re.match(r"^(\d{4}/\d{2})\d*$", p)
        if m:
            return m.group(1)
        # Handle "Prel. 2024/25222" -> "Prel. 2024/25"
        m = re.match(r"^(Prel\.\s*\d{4}/\d{2})\d*$", p)
        if m:
            return m.group(1)
        # Handle "2025/26Proj.111" -> "2025/26 Proj."
        m = re.match(r"^(\d{4}/\d{2})(Proj\.?)\d*$", p)
        if m:
            return f"{m.group(1)} {m.group(2)}"
        # Handle "Nov333" -> "Nov"
        m = re.match(r"^(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\d*$", p)
        if m:
            return m.group(1)
        return p

    period_line = lines[5].split(",") if len(lines) > 5 else []
    sub_period_line = lines[6].split(",") if len(lines) > 6 else []

    # Build periods list
    periods = []
    for i, p in enumerate(period_line[1:5]):
        _p = clean_period(p)
        if _p:
            # Check if there's a sub-period (Nov, Dec)
            sub = (
                clean_period(sub_period_line[i + 1])
                if i + 1 < len(sub_period_line)
                else ""
            )
            if sub and sub in ("Nov", "Dec", "Jan", "Feb", "Mar"):
                periods.append(f"{_p} {sub}")
            else:
                periods.append(_p)

    if not periods:
        return {
            "report": report_title,
            "template": 9,
            "row_count": 0,
            "data": [],
            "error": "Could not extract periods from CSV",
        }

    data = []
    current_commodity = None

    for line in lines[9:]:
        if not line.strip():
            continue

        parts = line.split(",")
        first_col = parts[0].strip()
        values = parts[1:]

        has_data = any(parse_value(v) is not None for v in values)

        # Commodity header
        if first_col and not has_data:
            current_commodity = first_col
            continue

        if not first_col:
            continue

        country = first_col

        # Determine region/country using helper
        region_val, country_val = set_region_country(country, None)

        for i, period in enumerate(periods[:4]):
            if i < len(values):
                val = parse_value(values[i])
                if val is not None:
                    data.append(
                        {
                            "region": region_val,
                            "country": country_val,
                            "commodity": current_commodity,
                            "attribute": "Production",
                            "marketing_year": period,
                            "value": val,
                            "unit": unit,
                        }
                    )

        # Change values
        latest_period = periods[-1] if periods else "Unknown"
        if len(values) > 4 and parse_value(values[4]) is not None:
            data.append(
                {
                    "region": region_val,
                    "country": country_val,
                    "commodity": current_commodity,
                    "attribute": "Change from Last Month",
                    "marketing_year": latest_period,
                    "value": parse_value(values[4]),
                    "unit": unit,
                }
            )
        if len(values) > 5 and parse_value(values[5]) is not None:
            data.append(
                {
                    "region": region_val,
                    "country": country_val,
                    "commodity": current_commodity,
                    "attribute": "Change from Last Month (%)",
                    "marketing_year": latest_period,
                    "value": parse_value(values[5]),
                    "unit": "%",
                }
            )

    return {"report": report_title, "template": 9, "row_count": len(data), "data": data}