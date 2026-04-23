def is_data_row_header(row):
    """Check if a row from data array is a header/title row that should be skipped."""
    non_empty = [c.strip() for c in row if c.strip()]
    if not non_empty:
        return True  # Empty row - skip

    row_text = " ".join(non_empty)

    # Title rows: "For the Years Ended...", "Unaudited", etc.
    # BUT only if the row has NO numeric data values.  Rows like
    # "Three months ended April 30, | 10 | $273.42 | $2,681" are DATA
    # rows whose first cell happens to contain "months ended" as a
    # label — they must NOT be skipped.
    if re.search(
        r"(years?\s+ended|months?\s+ended|weeks?\s+ended|unaudited|as of)",
        row_text,
        re.I,
    ):
        has_numeric_data = any(
            re.match(
                r"^[+\-]?[\$]?\(?\$?\s*[\d,]+\.?\d*\s*\)?%?$",
                c.strip(),
            )
            for c in non_empty
            if not re.match(r"^(19|20)\d{2}$", c.strip())  # Exclude years
        )
        if not has_numeric_data:
            return True

    # Check if this is a category header row (ALL CAPS words, no numbers)
    # EQUIPMENT, OPERATIONS, FINANCIAL, SERVICES, ELIMINATIONS, CONSOLIDATED
    all_caps_count = sum(1 for c in non_empty if re.match(r"^[A-Z]{2,}$", c))

    if all_caps_count >= 2 and not any(re.search(r"\d", c) for c in non_empty):
        return True

    # Year-only rows: just years like 2025, 2024, 2023
    year_count = sum(1 for c in non_empty if re.match(r"^(19|20)\d{2}$", c))

    if year_count >= 2 and year_count == len(non_empty):
        return True

    # Period rows: "May 1999", "November 1998", "Q1 2024",
    # "September 26, 2025", "Oct 27, 2024", etc.
    # These are date/period headers that should be skipped if they're ALL dates
    period_pattern = (
        r"^(?:January|February|March|April|May|June|July|August|"
        r"September|October|November|December|"
        r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec|"
        r"Q[1-4]|H[12])"
        r"[\s.,]*(?:\d{1,2}[\s,]*)?\d{4}$"
    )
    period_count = sum(1 for c in non_empty if re.match(period_pattern, c, re.I))

    return bool(period_count >= 2 and period_count == len(non_empty))