def _is_continuation_table(table, prev_table=None):
    """Check if this table is a continuation of a previous table.

    Returns True if the table's first non-empty row is just a year like "2024" or "2023"
    AND the column count matches the previous table (if provided).

    Also returns True for "headerless continuations": tables that have no header
    rows (no years), start directly with data rows (containing dollar/numeric values),
    have the same expanded column count as prev_table, and are immediate DOM siblings.
    """
    rows = table.find_all("tr")
    is_year_only_start = False
    for row in rows[:3]:  # Check first 3 rows
        cells = row.find_all(["td", "th"])
        non_empty = []
        for cell in cells:
            text = cell.get_text().replace("\u200b", "").replace("\xa0", " ").strip()
            if text:
                non_empty.append(text)
        if not non_empty:
            continue
        # If first non-empty row has just one cell and it's a year
        if len(non_empty) == 1 and re.match(r"^(19|20)\d{2}$", non_empty[0]):
            is_year_only_start = True
            break
        # If has multiple cells but first is a year and rest are empty/whitespace
        break

    if is_year_only_start:
        # Original year-only continuation check
        if prev_table is not None:
            prev_cols = _count_data_columns(prev_table)
            this_cols = _count_data_columns(table)
            if prev_cols > 0 and this_cols > 0 and prev_cols != this_cols:
                return False
        return True

    # ── Headerless continuation detection ──────────────────────────────
    # A table that has NO header rows but matching column structure is
    # likely a page-break continuation of the previous table.
    if prev_table is None:
        return False

    # 1. Check that they are immediate DOM siblings (no significant content between)
    if not _are_immediate_sibling_tables(prev_table, table):
        return False

    # 2. Must have matching expanded column counts
    prev_width = _expanded_col_count(prev_table)
    this_width = _expanded_col_count(table)
    if prev_width == 0 or this_width == 0 or prev_width != this_width:
        return False

    # 3. Must have NO header row (no years or period phrases in the first
    #    non-empty row that would indicate an independent table)
    for row in rows[:3]:
        cells = row.find_all(["td", "th"])
        non_empty = []
        for cell in cells:
            text = cell.get_text().replace("\u200b", "").replace("\xa0", " ").strip()
            if text:
                non_empty.append(text)
        if not non_empty:
            continue
        # If ANY cell is a year or period phrase, it has its own header
        for t in non_empty:
            if re.match(r"^(19|20)\d{2}$", t):
                return False
            if re.search(
                r"(months?\s+ended|year\s+ended|quarter\s+ended|weeks?\s+ended)",
                t,
                re.I,
            ):
                return False
        break

    # 4. At least one of the first several rows must look like a data row
    #    (contains a dollar sign, or 2+ numeric/percentage cells).
    #    This allows section label rows (e.g., "Investment banking fees")
    #    to precede the actual data without blocking detection,
    #    while avoiding false merges on TOC tables (single page-number cells).
    for row in rows[:10]:
        cells = row.find_all(["td", "th"])
        texts = []
        for cell in cells:
            text = cell.get_text().replace("\u200b", "").replace("\xa0", " ").strip()
            if text:
                texts.append(text)
        if not texts:
            continue
        has_dollar = any("$" in t for t in texts)
        if has_dollar:
            return True
        numeric_count = sum(
            1
            for t in texts
            if t not in ("—", "-", "–")
            and re.match(r"^[\$\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t)
        )
        if numeric_count >= 2:
            return True

    return False