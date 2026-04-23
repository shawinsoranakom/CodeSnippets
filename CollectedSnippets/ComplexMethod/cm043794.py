def _split_composite_table(table) -> list:
    """Split a single <table> that contains multiple sub-tables.

    Certent CDM and similar absolute-position SEC filings often group
    several logical tables (e.g. TABLE 5, TABLE 6, TABLE 7) plus
    connecting body-text paragraphs into **one** horizontal-rule zone,
    so ``_build_table_from_zone`` emits a single ``<table>`` for the
    whole lot.

    This function detects "TABLE X:" header rows and splits the
    original table element into a list of ``(rows, is_body_text)``
    tuples.  Each ``rows`` list is a contiguous slice of ``<tr>``
    elements.  ``is_body_text`` is True when the section between two
    TABLE headers consists entirely of single-cell (full-width) text
    rows that should be rendered as paragraphs rather than a table.

    Returns a list of BS4 ``<table>`` elements (and plain-text string
    fragments for body-text sections) ready for independent conversion.
    """
    all_rows = table.find_all("tr")
    if len(all_rows) < 4:
        return [table]

    # Find rows whose first cell matches "TABLE X: …"
    split_indices: list[int] = []
    for idx, row in enumerate(all_rows):
        cells = row.find_all(["td", "th"])
        if not cells:
            continue
        first_text = cells[0].get_text(strip=True)
        if _TABLE_TITLE_RE.match(first_text):
            split_indices.append(idx)

    # Need at least 2 sub-table headers to justify splitting
    if len(split_indices) < 2:
        return [table]

    # Helper: detect if a row-set is purely body text
    # (all data in column 0, rest empty)
    def _is_body_text_section(rows):
        if not rows:
            return True
        for row in rows:
            cells = row.find_all(["td", "th"])
            # Check if any cell beyond the first has content
            if any(c.get_text(strip=True) for c in cells[1:]):
                return False
        return True

    # Build segments: each segment is a slice of rows
    # Segments between TABLE headers that are all single-cell → body text
    # TABLE header row + data rows after it → sub-table
    parts: list = []

    # Rows before the first TABLE header (belong to whatever table was at top)
    if split_indices[0] > 0:
        pre_rows = all_rows[: split_indices[0]]
        # Check if there's a "TABLE X:" in the very first rows
        # If so, this is the main table data; otherwise check for body text
        sub = _make_sub_table(pre_rows, table)
        parts.append(sub)

    for si in range(len(split_indices)):
        start = split_indices[si]
        end = split_indices[si + 1] if si + 1 < len(split_indices) else len(all_rows)

        # Find where body text starts between this and next TABLE header
        # The sub-table continues until rows become single-cell body text
        sub_rows = all_rows[start:end]

        # Within this slice, find where the data rows end and body text begins
        # Body text: every cell after col 0 is empty AND text is long (>60 chars),
        # OR an all-caps heading followed by body text paragraphs.
        data_end = len(sub_rows)
        for ri in range(1, len(sub_rows)):
            row = sub_rows[ri]
            cells = row.find_all(["td", "th"])
            first = cells[0].get_text(strip=True) if cells else ""
            rest_empty = not any(c.get_text(strip=True) for c in cells[1:])
            if not rest_empty or not first:
                continue
            if _TABLE_TITLE_RE.match(first):
                continue

            # Long body text paragraph
            is_body_start = len(first) > 60
            # Or: all-caps section heading followed by body text
            if not is_body_start and first.isupper() and len(first) > 5:
                # Check if the NEXT row is long body text
                ni = ri + 1
                if ni < len(sub_rows):
                    ncells = sub_rows[ni].find_all(["td", "th"])
                    nfirst = ncells[0].get_text(strip=True) if ncells else ""
                    nrest = not any(c.get_text(strip=True) for c in ncells[1:])
                    if nrest and len(nfirst) > 60:
                        is_body_start = True

            if is_body_start:
                remaining = sub_rows[ri:]
                if _is_body_text_section(remaining):
                    data_end = ri
                    break

        # Table data part
        table_rows = sub_rows[:data_end]
        if table_rows:
            parts.append(_make_sub_table(table_rows, table))

        # Body text part
        if data_end < len(sub_rows):
            body_rows = sub_rows[data_end:]
            body_text = "\n".join(
                row.find_all(["td", "th"])[0].get_text(strip=True)
                for row in body_rows
                if row.find_all(["td", "th"])
                and row.find_all(["td", "th"])[0].get_text(strip=True)
            )
            if body_text.strip():
                parts.append(body_text)

    return parts