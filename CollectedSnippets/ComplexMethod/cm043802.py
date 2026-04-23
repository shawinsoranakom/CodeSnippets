def _classify_table(table_elem) -> str:
    """
    Unified table classifier. Returns one of:
    - "BULLET": Table with bullet characters → extract as bullet list
    - "FOOTNOTE": Table with footnote markers (*, (1), (a)) → extract as text
    - "HEADER": Single-cell section header → extract as markdown header
    - "DATA": Everything else → render as markdown table (DEFAULT)

    The key principle: be CONSERVATIVE about extracting as text.
    When in doubt, render as a table. Tables are data; don't lose structure.
    """
    rows = table_elem.find_all("tr")
    if not rows:
        return "DATA"

    # Collect info about the table structure
    non_empty_rows = []
    for row in rows:
        cells = row.find_all(["td", "th"])
        cell_texts = [c.get_text(strip=True) for c in cells]
        non_empty_texts = [t for t in cell_texts if t]
        if non_empty_texts:
            non_empty_rows.append((cells, non_empty_texts))

    if not non_empty_rows:
        return "DATA"

    # Check for bullet list (actual bullet characters, not asterisk which is a footnote marker)
    bullet_rows = 0
    for cells, texts in non_empty_rows:
        for text in texts[:2]:
            if text in BULLET_CHARS:
                bullet_rows += 1
                break

    if bullet_rows >= 1 and bullet_rows >= len(non_empty_rows) * 0.5:
        return "BULLET"

    # ===== CHECK FOR FOOTNOTE TABLE =====
    # Table where first non-empty cell is a footnote marker
    # Markers: *, **, †, ‡, (1), (2), (a), (b), etc.
    footnote_pattern = re.compile(r"^[\*†‡§¶]+$|^\(\d+\)$|^\([a-z]\)$|^\d+[\.\)]$")

    # Count rows that look like footnotes
    footnote_rows = 0
    for cells, texts in non_empty_rows:
        if len(texts) >= 2:
            first_text = texts[0]
            if footnote_pattern.match(first_text):
                footnote_rows += 1

    # If ALL multi-column rows are footnote-style, treat as footnote table.
    # Single-column rows are neutral continuation text (e.g. "The following
    # table sets forth the reconciliation...") and should not disqualify the
    # table from FOOTNOTE classification.
    candidate_rows = sum(1 for _, texts in non_empty_rows if len(texts) >= 2)
    if candidate_rows >= 1 and footnote_rows == candidate_rows:
        return "FOOTNOTE"

    # ===== CHECK FOR SECTION HEADER =====
    # Single row, single non-empty cell, typically bold or has id attribute
    if len(non_empty_rows) == 1:
        cells, texts = non_empty_rows[0]
        if len(texts) == 1:
            text = texts[0]
            cell = None
            for c in cells:
                if c.get_text(strip=True) == text:
                    cell = c
                    break

            if cell and len(text) < 100:
                # Check for header indicators
                has_toc_id = any(c.get("id", "").startswith("toc") for c in cells)
                is_bold = cell.find(["b", "strong"]) is not None
                # Also check for font-weight:bold in CSS
                if not is_bold:
                    is_bold = (
                        cell.find(
                            style=re.compile(r"font-weight:\s*bold", re.IGNORECASE)
                        )
                        is not None
                    )
                # If it looks like a section header, extract as header
                if has_toc_id or (is_bold and len(text) < 60):
                    return "HEADER"

    # ===== DEFAULT: DATA TABLE =====
    return "DATA"