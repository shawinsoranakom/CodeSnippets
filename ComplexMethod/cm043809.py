def is_header_row(parsed):
        """Check if this row is a header row (years or categories)."""

        # Filter truly empty cells and cells with only whitespace/invisible chars
        # Zero-width spaces (\u200b) and similar should be skipped
        def has_visible_content(t):
            # Remove zero-width spaces, zero-width non-joiners, etc.
            cleaned = (
                t.replace("\u200b", "")
                .replace("\u200c", "")
                .replace("\u200d", "")
                .replace("\ufeff", "")
                .strip()
            )
            return bool(cleaned)

        non_empty = [(t, c, s) for t, c, s in parsed if t and has_visible_content(t)]
        if not non_empty:
            return False, False  # empty, not header

        # Check if title row (one text spans >=80%)
        total_span = sum(c for t, c, s in parsed)
        max_span = max((c for t, c, s in non_empty), default=0)
        if max_span >= total_span * 0.8:
            # Don't classify date/year super-headers as title rows — even if a
            # date like "As of November 2007" spans ≥80% of the table width it
            # should still be treated as a year super-header row, not skipped.
            _spanning_text = next((t for t, c, s in non_empty if c == max_span), None)
            _is_date_span = _spanning_text and bool(
                re.search(
                    rf"(?:As\s+of\s+)?(?:{MONTHS_PATTERN}\s+)?(?:\d{{1,2}},?\s*)?(19|20)\d{{2}}\b",
                    _spanning_text,
                    re.I,
                )
            )
            if not _is_date_span:
                return False, True  # title row - skip but count

        # Check for period description rows like "For the Three Months Ended..."
        # These are single-cell descriptions that should be treated as title rows
        if len(non_empty) == 1:
            text, colspan, start = non_empty[0]
            # Period descriptions in first column with phrases like "For the X Months/Weeks/Years Ended"
            if start == 0 and re.search(
                r"for\s+the\s+(\w+\s+)?(months?|weeks?|quarters?|years?|period)\s+ended",
                text,
                re.I,
            ):
                return False, True  # title row - skip but count

            # A single non-empty cell at position 0 that does NOT
            # reference any year or date is a table title / section
            # label (e.g. "Financial performance of JPMorganChase"),
            # NOT a category header.  Category headers appear at
            # start > 0 spanning data columns, typically with multiple
            # cells per row.  Mis-classifying titles as categories
            # breaks the header scan — it causes the scanner to stop
            # at the very next non-header row, never reaching the
            # actual year/period row further down.
            if (
                start == 0
                and not re.search(r"\b(19|20)\d{2}\b", text)
                and not re.search(
                    rf"(months?\s+ended|year\s+ended|weeks?\s+ended"
                    rf"|{MONTHS_PATTERN}\s+\d{{1,2}})",
                    text,
                    re.I,
                )
            ):
                return False, True  # title row - skip but count

        has_year = False
        has_category = False
        has_data = False
        has_label = False  # Line item label (text in col 0/1 with small colspan)

        for t, colspan, start in non_empty:
            if t.startswith("(") and ("million" in t.lower() or "except" in t.lower()):
                continue

            # Check for year before checking for numeric data
            if is_year(t):
                has_year = True
            elif re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t):
                # At position 0 (label column), a bare small number
                # (1-3 digits with no financial formatting) may be a
                # rendering artifact rather than a data value.
                if start == 0 and re.match(r"^\d{1,3}$", t):
                    continue
                has_data = True
                break
            elif start > 0 and re.search(
                rf"(months?\s+ended|year\s+ended|weeks?\s+ended|quarters?\s+ended"
                rf"|ended\s+{MONTHS_PATTERN}|{MONTHS_PATTERN}\s+\d{{1,2}}\s*,?(?:\s*(?:19|20)\d{{2}})?"
                rf"|(?:As\s+of\s+)?{MONTHS_PATTERN}\s+(19|20)\d{{2}}\b)",
                t,
                re.I,
            ):
                # Catches "Three Months Ended May 31" / "January 26, 2025" / "Ended November"
                # / "November 2007" / "As of November 2007" / "October 31," (bare date fragment)
                # but NOT standalone unit labels like "Months", "Years", "10 Years"
                has_year = True
            elif is_category_text(t) and colspan >= 2:
                # Category headers can have colspan >= 2
                has_category = True
            elif is_category_text(t) and colspan == 1:
                # Category text with colspan=1 can also be a header
                # (e.g., "NUMBER OF SHARES UNDER OPTION" at start > 1)
                if start > 1:
                    has_category = True
            elif start <= 1 and colspan == 1 and len(t) > 3:
                # Text in first column with small colspan = line item label (data row)
                # Unless it's a very short text that could be a spacer
                has_label = True
            elif t.endswith(":"):
                # Section labels like "Assets:", "Liabilities:", "Revenues:" indicate data rows
                has_label = True

        # Data rows always stop header scanning
        if has_data:
            return False, False

        # If has_year or has_category, the label is just a row dimension header (e.g., "Risk Categories")
        if has_label and not (has_year or has_category):
            return False, False

        # Staircase top-row: all non-empty cells in data columns (start > 0) with
        # uniform small colspan and no financial data.  Catches maturity-range
        # labels like "0 - 6", "6 - 12", "10 Years" that fail every single-cell
        # test but are clearly split column headers when they appear together with
        # equal colspan (e.g., all colspan=2 spanning gutter+value pairs).
        if not has_year and not has_category and not has_label:
            data_col_cells = [(t, c, s) for t, c, s in non_empty if s > 0]
            if (
                len(data_col_cells) >= 2
                and len({c for _, c, _ in data_col_cells}) == 1  # uniform colspan
                and data_col_cells[0][1] >= 2  # not colspan-1 label cells
            ):
                has_category = True

        return (has_year or has_category), False