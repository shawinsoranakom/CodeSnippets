def build_column_headers_from_colspan(rows_with_colspan, _year_pos_shift):
    """Build proper multi-index column headers.

    For tables with stacked category headers like:
        Row 0: [Title spanning all columns - SKIP]
        Row 1: "" | "EQUIPMENT" (colspan=8) | "FINANCIAL" (colspan=8) | ...
        Row 2: "" | "OPERATIONS" (colspan=8) | "SERVICES" (colspan=8) | "ELIMINATIONS" | "CONSOLIDATED"
        Row 3: "" | "2025" | "2024" | "2023" | "2025" | "2024" | "2023" | ...

    Output multi-index format:
        Row 1: ["", "EQUIPMENT OPERATIONS", "", "", "FINANCIAL SERVICES", "", "", ...]
        Row 2: ["", "2025", "2024", "2023", "2025", "2024", "2023", ...]

    POSITION-BASED vertical merge: if row N and row N+1 both have text at same
    column position with large colspan, merge them into one category name.
    Category name appears ONLY in the first cell of its span, not repeated.

    Returns (header_layers, header_row_count)

    ``_year_pos_shift`` is a one-element list used as a mutable output
    parameter so the caller can read back the computed shift value.  When
    called outside of ``convert_table`` (e.g. in tests) it may be ``None``; in
    that case a local list is used so the function still works correctly.

    """
    if not rows_with_colspan:
        return None, 0

    # Extract colspan structure and text for each row
    # Structure: list of (text, colspan, start_col) tuples
    parsed_rows = []
    for row in rows_with_colspan:
        parsed = []
        col_pos = 0
        for text, colspan in row:
            stripped_text = text.strip()
            parsed.append((stripped_text, colspan, col_pos))
            col_pos += colspan
        parsed_rows.append(parsed)

    if not parsed_rows:
        return None, 0

    def is_year(t):
        # Strip trailing footnote markers like *, **, †, ‡, §
        t_clean = re.sub(r"[*†‡§+]+$", "", t.strip())
        return bool(re.match(r"^(19|20)\d{2}$", t_clean))

    def is_category_text(t):
        """Check if text looks like a category header (not a year, not data)."""
        if not t or is_year(t):
            return False
        # Remove <br> tags before checking patterns (multi-line headers)
        t_clean = re.sub(r"<[Bb][Rr]\s*/?>", " ", t).strip()
        t_clean = re.sub(r"\s+", " ", t_clean)  # Collapse whitespace
        # Remove trailing footnote markers like *, **, *+, **+
        t_clean = re.sub(r"\s*[\*+]+$", "", t_clean)
        # Remove trailing superscript footnote numbers like "1,2,3" or "4"
        # These come from <sup> tags concatenated with the text
        t_clean = re.sub(r"\s+\d+(?:,\d+)*$", "", t_clean)
        # Also strip footnote digits directly attached to words (no whitespace)
        # e.g., "Net Interest2" → "Net Interest", "All Other3" → "All Other"
        t_clean = re.sub(r"(?<=[A-Za-z])\d+$", "", t_clean)
        if re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t_clean):
            return False  # It's data
        # Title Case: "Equipment Operations", "Operating Income/(Loss)"
        # Strip /()\- before checking to avoid catastrophic backtracking
        t_stripped = re.sub(r"[/()\-]", " ", t_clean)
        t_stripped = re.sub(r"\s+", " ", t_stripped).strip()
        # Also prepare a variant with leading symbol prefixes removed
        # so that headers like "% Average rate" or "# of Shares" are
        # recognized after stripping the leading punctuation.
        t_no_prefix = re.sub(r"^[%#$&*~!@^]+\s*", "", t_stripped)
        if (
            re.match(r"^[A-Z][A-Za-z]*(\s+[A-Za-z&]+)*$", t_stripped)
            and len(t_clean) > 2
        ):
            return True
        if (
            t_no_prefix != t_stripped
            and re.match(r"^[A-Z][A-Za-z]*(\s+[A-Za-z&]+)*$", t_no_prefix)
            and len(t_no_prefix) > 2
        ):
            return True
        # ALL CAPS: "EQUIPMENT", "FINANCIAL SERVICES", "LONG-LIVED ASSETS"
        if re.match(r"^[A-Z]{2,}(-[A-Z]+)?(\s+[A-Z]+(-[A-Z]+)?)*$", t_clean):
            return True
        # ALL CAPS with periods/abbreviations: "WTD. AVG. EXERCISE PRICE", "NO. OF SHARES"
        # Pattern: uppercase word (optionally with period) followed by more words
        if (
            re.match(r"^[A-Z]{2,}\.?(\s+[A-Z]{2,}\.?)*(\s+[A-Z]+)*$", t_clean)
            and len(t_clean) > 3
        ):
            return True
        # Abbreviated ALL-CAPS with dots and dashes: "YR.-TO-YR."
        if re.match(r"^[A-Z]{2,}\.(-[A-Z]{2,}\.?)+$", t_clean):
            return True
        # Abbreviations like "U.S.", "NON-U.S.", "U.K." - single letters with periods
        # Pattern: optional prefix (NON-), then letter-period pairs
        if re.match(r"^([A-Z]+-)?[A-Z]\.[A-Z]\.?$", t_clean):
            return True
        # Abbreviations followed by words: "U.S. PLANS", "NON-U.S. PLANS"
        if re.match(r"^([A-Z]+-)?[A-Z]\.[A-Z]\.?(\s+[A-Z]+)+$", t_clean):
            return True
        # Hyphenated categories: "NON-GAAP", "PRE-TAX"
        if re.match(r"^[A-Z]+-[A-Z]+$", t_clean):
            return True
        # Hyphenated words followed by more words: "PPP-QUALIFIED PORTION"
        return bool(re.match(r"^[A-Z]+-[A-Z]+(\s+[A-Z]+)+$", t_clean))

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

    # First pass: identify all header rows and classify them
    header_info: list = []  # (row_idx, parsed, is_year_row, is_category_row)
    header_row_count = 0

    def has_visible_text(t):
        cleaned = (
            t.replace("\u200b", "")
            .replace("\u200c", "")
            .replace("\u200d", "")
            .replace("\ufeff", "")
            .strip()
        )
        return bool(cleaned)

    title_period_texts = []  # Track period titles for super-header use

    for row_idx, parsed in enumerate(parsed_rows):
        is_header, is_title = is_header_row(parsed)
        # Check if this row is completely empty (all cells empty after stripping)
        non_empty_cells = [(t, c, s) for t, c, s in parsed if has_visible_text(t)]

        if not non_empty_cells:
            # Empty row - skip it but count it toward header_row_count
            header_row_count = row_idx + 1
            continue

        if is_title:
            # Save period/date titles for potential use as super-headers
            for _tt, _tc, _ts in parsed:
                if (
                    _tt
                    and has_visible_text(_tt)
                    and re.search(
                        rf"(months?|quarters?|years?|weeks?|period)\s+ended|ended\s+{MONTHS_PATTERN}|{MONTHS_PATTERN}\s+\d{{1,2}}",
                        _tt,
                        re.I,
                    )
                ):
                    title_period_texts.append(_tt)
            header_row_count = row_idx + 1
            continue

        if not is_header:
            # Before breaking, check if this is a pre-header title row.
            # SEC filings often have company names and statement titles
            # in single cells at position 0 without large colspan.
            # These should be skipped before any real headers are found.
            if not header_info:  # No headers found yet
                non_empty_check = [
                    (t, c, s) for t, c, s in parsed if has_visible_text(t)
                ]
                if len(non_empty_check) <= 1 and (
                    not non_empty_check
                    or non_empty_check[0][2] == 0
                    or non_empty_check[0][1]
                    > 2  # Large colspan = title at any position
                ):
                    # Single text at position 0 (or empty) or with large colspan before headers → title row
                    header_row_count = row_idx + 1
                    continue
            break  # Hit actual data row

        # After year rows have been found, a single-cell row at position 0
        # is a section header (e.g., "Assets", "Liabilities"), not a column
        # category. Stop scanning for headers.
        if header_info:
            has_year_already = any(is_yr for _, _, is_yr, _ in header_info)
            if (
                has_year_already
                and len(non_empty_cells) == 1
                and non_empty_cells[0][2] == 0
            ):
                break

        # Classify: year row or category row?
        non_empty = [(t, c, s) for t, c, s in parsed if has_visible_text(t)]

        # Check if this row has large-colspan period phrases (super-headers)
        # E.g., "Three Months Ended May"[cs=7] is a category spanning year columns
        has_large_colspan_period = any(
            colspan > 2
            and re.search(
                rf"(months?|quarters?|years?|weeks?)\s+ended|ended\s+{MONTHS_PATTERN}",
                t,
                re.I,
            )
            for t, colspan, s in non_empty
        )

        has_year = any(
            is_year(t)
            or (
                re.search(rf"(ended|{MONTHS_PATTERN})", t, re.I)
                and colspan <= 2
                and s > 0  # Skip first column (row labels like "AT DECEMBER 31:")
            )
            or (
                # Full dates like "January 26, 2025", "September 26,2025",
                # or "September 26,<br>2025" (with <br> tag) are year indicators
                re.search(
                    rf"({MONTHS_PATTERN})\s+\d{{1,2}},?\s*(19|20)\d{{2}}",
                    re.sub(r"<[Bb][Rr]\s*/?>", " ", t),
                    re.I,
                )
                and s > 0
            )
            or (
                # "Month YYYY" (no day) or "As of Month YYYY" — period super-headers
                # with any colspan (e.g. "As of November 2007" cs=22 spans whole table)
                re.search(
                    rf"(?:As\s+of\s+)?{MONTHS_PATTERN}\s+(19|20)\d{{2}}\b",
                    t,
                    re.I,
                )
                and s > 0
            )
            for t, colspan, s in non_empty
        )
        has_category = any(
            is_category_text(t) and not is_year(t) for t, c, s in non_empty
        )

        # Large-colspan period phrases are treated as categories
        if has_large_colspan_period:
            period_phrases_have_year = any(
                colspan > 2
                and re.search(
                    rf"(months?|quarters?|years?|weeks?)\s+ended|ended\s+{MONTHS_PATTERN}",
                    t,
                    re.I,
                )
                and re.search(
                    r"\b(19|20)\d{2}\b",
                    re.sub(r"<[Bb][Rr]\s*/?>", " ", t),
                )
                for t, colspan, s in non_empty
            )
            if not period_phrases_have_year:
                has_year = False
            has_category = True

        header_info.append((row_idx, parsed, has_year, has_category))
        header_row_count = row_idx + 1

    if not header_info:
        return None, 0

    # A valid financial table must have at least one data row after
    # the header region, so bail out and let the caller fall back to
    # simple non-financial table processing.
    if header_row_count >= len(parsed_rows):
        return None, 0

    # Separate category rows and year rows
    category_rows = [
        (idx, p) for idx, p, is_yr, is_cat in header_info if is_cat and not is_yr
    ]
    year_rows = [(idx, p) for idx, p, is_yr, is_cat in header_info if is_yr]

    # Extract column headers from year rows
    column_headers_list = []
    column_headers_positions = []

    for row_idx, parsed in year_rows:
        for text, colspan, start in parsed:
            if not text:
                continue

            if start == 0 and not is_year(text):
                continue

            # Skip notes/descriptors in parentheses
            if text.startswith("(") and (
                "million" in text.lower() or "except" in text.lower()
            ):
                continue

            column_headers_list.append(text)
            column_headers_positions.append(start)

    # When the first year header is at position 0 (occupying the label
    # column), it means the year sub-header row lacks a separate label
    # cell — years start from the very first cell.  Data rows DO have
    # a label at position 0, so data values start at a later position.
    # Shift all year header positions right by the label column width
    # (= first category position) to align them with data columns.
    # ``_year_pos_shift`` may be None when the function is called outside
    # of convert_table (e.g. in tests); in that case use a local list.
    if _year_pos_shift is None:
        _year_pos_shift = [0]
    _year_pos_shift[0] = 0
    if column_headers_positions and column_headers_positions[0] == 0 and category_rows:
        # Use first category's start position as the label width
        for _, cat_parsed in category_rows:
            for _ct, _cc, _cs in cat_parsed:
                if _cs > 0:
                    _year_pos_shift[0] = _cs
                    break
            break
        if _year_pos_shift[0] > 0:
            column_headers_positions = [
                p + _year_pos_shift[0] for p in column_headers_positions
            ]

    # Check for stacked date + year header pattern:
    # Row A: "January 26," "October 27," "January 28," (dates with months)
    # Row B: "2025" "2024" "2024" (years)
    # Should combine to: "January 26, 2025", "October 27, 2024", etc.
    # Also handles extra non-month/non-year items at different positions:
    # Row A: "January 26" "January 28" "%"
    # Row B: "2025" "2024" "Change"
    # -> "January 26, 2025" "January 28, 2024" "% Change"
    if len(year_rows) >= 2:

        def _row_headers(parsed_row):
            result = []
            for text, _, start in parsed_row:
                t = text.strip()
                if not t:
                    continue
                # Skip first-column labels but allow years at position 0
                if start == 0 and not is_year(t):
                    continue
                if t.startswith("(") and (
                    "million" in t.lower() or "except" in t.lower()
                ):
                    continue
                result.append((t, start))
            return result

        def _try_position_merge(hdrs_a, hdrs_b):
            """Try to merge two header rows by matching positions.
            Returns (merged_texts, merged_positions) sorted by position,
            or (None, None) if no month+year merges found.
            """
            # Build position maps
            pos_a = {s: t for t, s in hdrs_a}
            pos_b = {s: t for t, s in hdrs_b}
            all_positions = sorted(set(pos_a.keys()) | set(pos_b.keys()))

            merged = []
            merged_pos = []
            month_year_merges = 0
            for pos in all_positions:
                text_a = pos_a.get(pos)
                text_b = pos_b.get(pos)
                if text_a and text_b:
                    a_is_month = bool(re.search(MONTHS_PATTERN, text_a, re.I))
                    b_is_year = is_year(text_b)
                    a_is_year = is_year(text_a)
                    b_is_month = bool(re.search(MONTHS_PATTERN, text_b, re.I))
                    if a_is_month and b_is_year:
                        merged.append(f"{text_a.rstrip(',').strip()}, {text_b}")
                        month_year_merges += 1
                    elif a_is_year and b_is_month:
                        merged.append(f"{text_b.rstrip(',').strip()}, {text_a}")
                        month_year_merges += 1
                    else:
                        # Generic vertical merge (e.g., "%" + "Change" -> "% Change")
                        merged.append(f"{text_a} {text_b}".strip())
                elif text_a:
                    merged.append(text_a)
                elif text_b:
                    merged.append(text_b)
                merged_pos.append(pos)

            if month_year_merges > 0:
                return merged, merged_pos
            return None, None

        for i in range(len(year_rows)):
            for j in range(i + 1, len(year_rows)):
                _, row_a = year_rows[i]
                _, row_b = year_rows[j]
                hdrs_a = _row_headers(row_a)
                hdrs_b = _row_headers(row_b)

                if len(hdrs_a) == 0 or len(hdrs_b) == 0:
                    continue

                # Check that at least one row has months and at least one has years
                a_has_months = any(
                    re.search(MONTHS_PATTERN, h, re.I) for h, _ in hdrs_a
                )
                b_has_months = any(
                    re.search(MONTHS_PATTERN, h, re.I) for h, _ in hdrs_b
                )
                a_has_years = any(is_year(h) for h, _ in hdrs_a)
                b_has_years = any(is_year(h) for h, _ in hdrs_b)

                if (a_has_months and b_has_years) or (a_has_years and b_has_months):
                    result, result_positions = _try_position_merge(hdrs_a, hdrs_b)
                    if result:
                        column_headers_list = result
                        column_headers_positions = result_positions
                        break
            else:
                continue
            break

    if not column_headers_list:
        # No year row headers found
        # Check for date-super-header pattern: one category row is a single
        # large-colspan date/period phrase spanning everything, and remaining
        # category rows have vertically-stacked text sub-column headers.
        # Example:
        #   Row 0: "Three Months Ended January 26, 2025" cs=11  (super-header)
        #   Row 1: "Retail Notes" cs=2, "Revolving" cs=2
        #   Row 2: "& Financing" cs=2, "Charge" cs=2, "Wholesale" cs=2
        #   Row 3: "Leases" cs=2, "Accounts" cs=2, "Receivables" cs=2, "Total" cs=2
        #   → merge sub-columns: "Retail Notes & Financing Leases", etc.
        if len(category_rows) >= 2:
            _, first_parsed = category_rows[0]
            first_ne = [(t, c, s) for t, c, s in first_parsed if has_visible_text(t)]
            is_date_super = False
            super_text = ""
            if len(first_ne) == 1:
                super_text, super_cs, _ = first_ne[0]
                if super_cs > 2 and re.search(
                    rf"(months?|quarters?|years?|weeks?|period)\s+ended|ended\s+{MONTHS_PATTERN}|{MONTHS_PATTERN}\s+\d{{1,2}}",
                    super_text,
                    re.I,
                ):
                    is_date_super = True

            if is_date_super:
                # Vertically merge remaining category rows by position
                pos_texts: dict = {}  # col_pos -> [text1, text2, ...]
                for cat_idx in range(1, len(category_rows)):
                    _, sub_parsed = category_rows[cat_idx]
                    for sub_text, _, sub_start in sub_parsed:
                        if (
                            not sub_text
                            or not has_visible_text(sub_text)
                            or sub_start == 0
                        ):
                            continue
                        if sub_start not in pos_texts:
                            pos_texts[sub_start] = []
                        pos_texts[sub_start].append(sub_text)

                if pos_texts:
                    sorted_pos = sorted(pos_texts.keys())
                    merged_sub_headers = [" ".join(pos_texts[p]) for p in sorted_pos]
                    n_cols = len(merged_sub_headers)
                    # Build 2-layer header
                    super_row = ["", super_text]
                    for _ in range(n_cols - 1):
                        super_row.append("")
                    sub_row = [""] + merged_sub_headers
                    header_layers = [super_row, sub_row]
                    return header_layers, header_row_count

        # Fallback: check if category rows can serve as column headers (flat header table)
        # Merge by POSITION across all category rows.  When two rows
        # have text at the same position, the WIDER row (more total
        # columns) wins — it placed its header at an explicit position
        # in a full-width row.  The displaced text from the shorter
        # row is appended at the end (first uncovered position).
        # Example (MS 10-Q):
        #   R2 (18 cols): Net Interest2@9, All Other3@12
        #   R3 (12 cols): Trading@3, Fees1@6, Total@9
        #   → pos 9 conflict: R2 wins (wider), "Total" displaced to end
        #   → result: Trading | Fees1 | Net Interest2 | All Other3 | Total
        if category_rows:
            first_col_label = ""
            for _, cat_parsed in category_rows:
                for text, colspan, start in cat_parsed:
                    if start == 0 and text and not first_col_label:
                        first_col_label = text

            # Compute each row's total column span
            row_widths = []
            for _, cat_parsed in category_rows:
                total = sum(cs for _, cs, _ in cat_parsed)
                row_widths.append(total)

            # Build position -> (text, row_width) map.
            # Wider row wins at conflicts.
            pos_map = {}  # pos -> (text, row_width)
            displaced = []  # texts displaced from conflicts
            for cr_idx, (_, cat_parsed) in enumerate(category_rows):
                w = row_widths[cr_idx]
                for text, colspan, start in cat_parsed:
                    if start == 0 or not text:
                        continue
                    if start not in pos_map:
                        pos_map[start] = (text, w)
                    else:
                        existing_text, existing_w = pos_map[start]
                        if w > existing_w:
                            # New row is wider, it wins
                            displaced.append(existing_text)
                            pos_map[start] = (text, w)
                        elif w < existing_w:
                            # Existing row is wider, it keeps the position
                            displaced.append(text)
                        else:
                            # Same width — later row overrides (more specific)
                            displaced.append(existing_text)
                            pos_map[start] = (text, w)

            if pos_map:
                # Collect headers in position order
                final_headers = [pos_map[p][0] for p in sorted(pos_map.keys())]
                # Append displaced texts at the end
                final_headers.extend(displaced)

                n_cols = len(final_headers)
                header_layers = []

                if title_period_texts:
                    super_row = ["", title_period_texts[-1]] + [""] * (n_cols - 1)
                    header_layers.append(super_row)

                header_row = [first_col_label] + final_headers
                header_layers.append(header_row)
                return header_layers, header_row_count

        if not column_headers_list:
            # No year rows. If ≥ 2 category rows form a staircase (first row has
            # all cells in data columns with uniform colspan, like "0 - 6" / "6 - 12"
            # split from "Months" / "Months" below), merge them into one header row.
            if len(category_rows) >= 2:
                first_cat_parsed = category_rows[0][1]
                first_ne = [(t, c, s) for t, c, s in first_cat_parsed if t.strip()]
                first_is_staircase_top = (
                    first_ne
                    and all(s > 0 for _, _, s in first_ne)
                    and len({c for _, c, _ in first_ne}) == 1  # uniform colspan
                    and first_ne[0][1] >= 2  # colspan >= 2, not single-col labels
                )
                if first_is_staircase_top:
                    _sm_rows = []
                    for _, cat_parsed in category_rows:
                        sm: dict = {}
                        for text, colspan, start in cat_parsed:
                            t = (
                                text.replace("\u200b", "")
                                .replace("\u200c", "")
                                .replace("\ufeff", "")
                                .strip()
                            )
                            if t:
                                sm[start] = (t, start + colspan - 1)
                        if sm:
                            _sm_rows.append(sm)
                    if _sm_rows:
                        _leaf_pos = sorted(
                            p
                            for p in set().union(*[set(sm.keys()) for sm in _sm_rows])
                            if p > 0
                        )
                        if len(_leaf_pos) >= 1:
                            merged_cols = []
                            for lp in _leaf_pos:
                                parts: list = []
                                last_part: str | None = None
                                for sm in _sm_rows:
                                    for s, (txt, end) in sm.items():
                                        if s <= lp <= end:
                                            if txt != last_part:
                                                parts.append(txt)
                                                last_part = txt
                                            break
                                merged_cols.append(" ".join(parts) if parts else "")
                            # Label column: staircase-merge texts at position 0
                            first_col_parts: list = []
                            last_fc: str | None = None
                            for sm in _sm_rows:
                                if 0 in sm:
                                    txt, _ = sm[0]
                                    if txt != last_fc:
                                        first_col_parts.append(txt)
                                        last_fc = txt
                            first_col = " ".join(first_col_parts)
                            return [[first_col] + merged_cols], header_row_count
            # Still no headers — fall back
            return None, 0

    num_headers = len(column_headers_list)

    # Check for "year-as-super-header" pattern:
    # Row 0: years with LARGE colspan (e.g., "2003" cs=5, "2002" cs=5)
    #   OR full dates with LARGE colspan (e.g., "January 26, 2025" cs=5)
    # Row 1: sub-headers with smaller colspan (e.g., "BENEFIT OBLIGATION" cs=2)
    # Result: merge year/date + sub-header -> "2003 BENEFIT OBLIGATION", etc.
    year_super_headers = []  # [(year_text, start_col, end_col), ...]
    for row_idx, parsed in year_rows:
        for text, colspan, start in parsed:
            if not text:
                continue
            # Skip first-column labels, but allow years at position 0
            if start == 0 and not is_year(text):
                continue
            _text_clean = re.sub(r"<[Bb][Rr]\s*/?>", " ", text)
            # Bare year (e.g. "2007") OR full date (e.g. "November 26, 2007")
            _is_strong_date = is_year(text) or bool(
                re.search(
                    rf"({MONTHS_PATTERN})\s+\d{{1,2}},?\s*(19|20)\d{{2}}",
                    _text_clean,
                    re.I,
                )
            )
            # "Month YYYY" (no day) or "As of Month YYYY" — also a date
            _is_month_year = bool(
                re.search(
                    rf"(As\s+of\s+)?({MONTHS_PATTERN})\s+(19|20)\d{{2}}\b",
                    _text_clean,
                    re.I,
                )
            )
            # Require colspan > 2 for bare dates; >= 2 is enough when the
            # match is explicit (month+year or full date) since gutter tables
            # pack one data column into cs=2.
            if (_is_strong_date and colspan > 2) or (
                (_is_strong_date or _is_month_year) and colspan >= 2
            ):
                year_super_headers.append((text, start, start + colspan))

    # Guard: if category rows have LARGER colspans than the year
    # super-headers, then years are children of the categories, not
    # super-headers.  E.g. "Three Months Ended May" cs=7 contains
    # "1999" cs=3 and "1998" cs=3.  The standard category-distribution
    # path handles this correctly.
    # Check ALL non-empty cells in category rows (not just those passing
    # is_category_text), since period phrases like "Three Months Ended
    # October 31," are valid category headers but may fail the strict
    # is_category_text check due to trailing numbers/punctuation.
    if year_super_headers and category_rows:
        max_year_cs = max((end - start) for _, start, end in year_super_headers)
        max_cat_cs = 0
        for _, cat_parsed in category_rows:
            for _t, _c, _s in cat_parsed:
                if _t and _s > 0 and _c > max_cat_cs:
                    max_cat_cs = _c
        if max_cat_cs > max_year_cs:
            year_super_headers = []  # Not really super-headers

    # Allow the path even when header_info has only the year row itself
    # (no other rows classified as headers) — the lookahead block below will
    # discover staircase rows that failed is_header_row (e.g. "Assets / 0-6 / 6-12"
    # which has a label at col 0 and non-category column text).
    if year_super_headers and len(header_info) >= 1:
        year_row_indices = {idx for idx, _ in year_rows}

        # Pattern for words that are just date-label fragments (not real sub-headers).
        # A row made entirely of these is a continuation of a year label split
        # across two HTML rows (e.g., "As of" in row N, "November 2007" in row N+1).
        _date_frag_re = re.compile(
            rf"^(as(\s+of)?|of|through|ended|and|or)$"
            rf"|^{MONTHS_PATTERN}$"
            rf"|^(19|20)\d{{2}}$",
            re.I,
        )

        def _is_year_label_frag_row(parsed_row):
            """Return True if every non-empty text cell is a bare date word fragment."""
            text_vals = [
                txt.strip()
                for txt, _cs, _st in parsed_row
                if txt and txt.strip() and re.search(r"[A-Za-z]", txt)
            ]
            if not text_vals:
                return False
            return all(_date_frag_re.match(v) for v in text_vals)

        # Collect all non-year header rows found during the initial scan,
        # also excluding rows that are purely year-label fragment rows.
        sub_rows = [
            (idx, parsed)
            for idx, parsed, is_yr, is_cat in header_info
            if idx not in year_row_indices and not _is_year_label_frag_row(parsed)
        ]

        # Look ahead past header_row_count for additional staircase rows that
        # is_category_text() missed (e.g. "Owned, at", "Purchased, at" contain
        # commas which break the category-text regex).  Stop at first data row.
        lookahead_count = header_row_count
        for extra_idx in range(
            header_row_count, min(header_row_count + 10, len(parsed_rows))
        ):
            extra_parsed = parsed_rows[extra_idx]
            extra_ne = [(t, c, s) for t, c, s in extra_parsed if t and t.strip()]
            if not extra_ne:
                continue  # blank spacer row — keep looking
            # Any purely numeric cell means we have hit a data row
            has_numeric = any(
                re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t)
                for t, c, s in extra_ne
            )
            if has_numeric:
                break
            # Credit-rating / status values at data columns (start > 0) also
            # signal a data row.  These are short alphanumeric codes like F1,
            # A+, AA-, P-1, Stable, N/A that appear in ratings tables but are
            # NOT recognized by the numeric pattern above.
            _rating_re = re.compile(
                r"^(?:"
                r"[A-Z]{1,3}[+-]"  # A+, AA-, BBB+  (S&P/Fitch style)
                r"|[A-Z]{1,2}-\d"  # P-1, F-2       (Moody's/Fitch CP)
                r"|F\d[+-]?"  # F1, F1+        (Fitch specific)
                r"|[A-Z][a-z]{1,3}\d"  # Aa1, Baa2      (Moody's long-term)
                r"|Prime-\d"  # Prime-1
                r")$"
            )
            _status_words = {
                "stable",
                "positive",
                "negative",
                "watch",
                "developing",
                "n/a",
                "nm",
                "nr",
                "wd",
            }
            has_rating_data = any(
                (
                    _rating_re.match(t)
                    or t.upper() in ("N/A", "NM", "NR", "WD")
                    or t.lower() in _status_words
                )
                for t, c, s in extra_ne
                if s > 0  # only data columns, not the label column
            )
            if has_rating_data:
                break
            # Skip year-label fragment rows in the lookahead too
            if _is_year_label_frag_row(extra_parsed):
                continue
            # Must contain at least some letter-bearing cells (not just blanks/punct)
            text_cells = [
                (t, c, s) for t, c, s in extra_ne if re.search(r"[A-Za-z]", t)
            ]
            if text_cells:
                sub_rows.append((extra_idx, extra_parsed))
                lookahead_count = extra_idx + 1

        if sub_rows:
            # Build per-row start-maps: col_start -> (text, inclusive_end)
            row_start_maps: list = []
            for _, sub_parsed_row in sub_rows:
                sm = {}
                for text, colspan, start in sub_parsed_row:
                    t = (
                        text.replace("\u200b", "")
                        .replace("\u200c", "")
                        .replace("\u200d", "")
                        .replace("\ufeff", "")
                        .strip()
                    )
                    if t and re.search(r"[A-Za-z]", t):
                        sm[start] = (t, start + colspan - 1)
                    elif t and not re.match(
                        r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t
                    ):
                        # Also include non-alpha cells that are NOT plain financial
                        # data — e.g. maturity-range labels like "0 - 6", "1 - 5".
                        sm[start] = (t, start + colspan - 1)
                if sm:
                    row_start_maps.append(sm)

            if row_start_maps:
                # Leaf positions = union of all non-empty cell starts across
                # every staircase row — ensures cells that only appear in one
                # row (e.g. "Total" in the bottom leaf row) are not missed.
                # Always exclude position 0: it is the label/row-header column.
                leaf_positions_sub: list = sorted(
                    p
                    for p in set().union(*[set(sm.keys()) for sm in row_start_maps])
                    if p > 0
                )

                if len(leaf_positions_sub) >= 2:
                    # For each leaf position, walk every staircase row top-to-
                    # bottom collecting the cell that covers that position.
                    # Consecutive duplicates are suppressed so parent "2007"
                    # spanning both sub-columns doesn't repeat within a column.
                    # Date-fragment words (bare month names, "As of", "of" etc.)
                    # are skipped — they are split pieces of the year super-header
                    # label and must not contaminate sub-column names.
                    merged_subs: list = []
                    for leaf_pos in leaf_positions_sub:
                        parts = []
                        last_text = None
                        for sm in row_start_maps:
                            for start, (text, end) in sm.items():
                                if start <= leaf_pos <= end:
                                    if (
                                        not _date_frag_re.match(text)
                                        and text != last_text
                                    ):
                                        parts.append(text)
                                        last_text = text
                                    break
                        merged_subs.append(" ".join(parts) if parts else "")

                    # Determine whether position 0 is a label column.
                    # Merge staircase texts at position 0 the same way
                    # data columns do — e.g. "Assets" / "Contract Type"
                    # across two rows → "Assets Contract Type".
                    first_col_parts = []
                    last_first_col: str | None = None
                    for sm in row_start_maps:
                        if 0 in sm:
                            _fc_text, _fc_end = sm[0]
                            if (
                                not _date_frag_re.match(_fc_text)
                                and _fc_text != last_first_col
                            ):
                                first_col_parts.append(_fc_text)
                                last_first_col = _fc_text
                    first_col_label = (
                        " ".join(first_col_parts) if first_col_parts else ""
                    )

                    # Build year layer using position-based assignment:
                    # assign the year label to the FIRST leaf under each span,
                    # and "" for subsequent leaves under the same span.
                    # This correctly handles uneven splits like 4+1 rather
                    # than assuming equal distribution.

                    # Check whether this is a one-to-one mapping: every year
                    # span covers exactly ONE leaf position.  In that case the
                    # year cell and the sub-header cell at the same position
                    # together form ONE column name (e.g. "As of" + "November
                    # 2007" → "As of November 2007").  Producing a two-layer
                    # structure would split them inappropriately.
                    _leaves_per_span = {
                        (ys, ye): sum(1 for lp in leaf_positions_sub if ys <= lp < ye)
                        for _yt, ys, ye in year_super_headers
                    }
                    _all_one_to_one = all(v == 1 for v in _leaves_per_span.values())

                    if _all_one_to_one:
                        # Single-layer mode: merge ALL staircase rows (sub-rows
                        # AND the year row) vertically per column position,
                        # without filtering date-fragment words — they are
                        # legitimate parts of the column label here.
                        _all_staircase = sorted(
                            sub_rows + list(year_rows),
                            key=lambda x: x[0],
                        )
                        flat_maps: list = []
                        for _, _row_parsed in _all_staircase:
                            _sm: dict = {}
                            for _txt, _cs, _st in _row_parsed:
                                _t = (
                                    _txt.replace("\u200b", "")
                                    .replace("\u200c", "")
                                    .replace("\ufeff", "")
                                    .strip()
                                )
                                if _t and (
                                    re.search(r"[A-Za-z0-9]", _t)
                                    and not re.match(
                                        r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$",
                                        _t,
                                    )
                                ):
                                    _sm[_st] = (_t, _st + _cs - 1)
                            if _sm:
                                flat_maps.append(_sm)

                        flat_subs: list = []
                        for leaf_pos in leaf_positions_sub:
                            _parts: list = []
                            _last: str | None = None
                            for _sm in flat_maps:
                                for _s, (_t, _end) in _sm.items():
                                    if _s <= leaf_pos <= _end:
                                        if _t != _last:
                                            _parts.append(_t)
                                            _last = _t
                                        break
                            flat_subs.append(" ".join(_parts) if _parts else "")

                        # Label column: merge position-0 texts from all rows
                        _fc_parts: list = []
                        _last_fc: str | None = None
                        for _sm in flat_maps:
                            if 0 in _sm:
                                _t, _ = _sm[0]
                                if _t != _last_fc:
                                    _fc_parts.append(_t)
                                    _last_fc = _t
                        _first_col = " ".join(_fc_parts)

                        return (
                            [[_first_col] + flat_subs],
                            max(header_row_count, lookahead_count),
                        )

                    year_row = [first_col_label]
                    seen_years: set = set()
                    for leaf_pos in leaf_positions_sub:
                        assigned_year = ""
                        for year_text, year_start, year_end in year_super_headers:
                            if year_start <= leaf_pos < year_end:
                                if year_text not in seen_years:
                                    assigned_year = year_text
                                    seen_years.add(year_text)
                                break
                        year_row.append(assigned_year)

                    sub_header_row_data = [first_col_label] + merged_subs
                    header_layers = [year_row, sub_header_row_data]
                    return header_layers, max(header_row_count, lookahead_count)

    # Extract categories with their positions, then merge vertically
    # Categories at same position merge: "EQUIPMENT" + "OPERATIONS" -> "EQUIPMENT OPERATIONS"
    # Only include cells with LARGE colspan (spanning multiple year columns)
    position_texts: dict = {}  # col_pos -> [text1, text2, ...]
    position_colspans: dict = {}  # col_pos -> colspan

    for row_idx, parsed in category_rows:
        for text, colspan, start in parsed:
            # Category headers must have large colspan (> 2) to span header columns
            if (
                text
                and colspan > 2
                and start > 0
                and (
                    is_category_text(text)
                    or re.search(
                        rf"(months?|quarters?|years?|weeks?)\s+ended|ended\s+{MONTHS_PATTERN}",
                        text,
                        re.I,
                    )
                )
            ):
                # Clean <br> tags from category text
                clean_text = re.sub(r"<[Bb][Rr]\s*/?>", " ", text).strip()
                clean_text = re.sub(r"\s+", " ", clean_text)
                if start not in position_texts:
                    position_texts[start] = []
                    position_colspans[start] = colspan
                else:
                    # Using the large parent colspan would incorrectly let the
                    # first child gobble up headers belonging to siblings.
                    position_colspans[start] = min(position_colspans[start], colspan)
                position_texts[start].append(clean_text)

    # Build merged categories in position order
    sorted_positions = sorted(position_texts.keys())
    categories = []  # [(merged_name, num_years_under), ...]

    for pos in sorted_positions:
        merged_name = " ".join(position_texts[pos])
        # Estimate headers under this category by colspan ratio
        # If all categories have same colspan, headers are evenly distributed
        categories.append(merged_name)

    # Collect "orphan" header cells from category rows — cells at
    # start > 0 that are NOT categories (failed is_category_text) and
    # NOT inside any recognized category's column span.  These are
    # independent column headers (e.g., "Balance Dec. 31, 2024")
    # that should appear as their own columns in the output.
    orphan_headers: list[tuple[str, int]] = []  # (text, start_pos)
    for _ri, parsed in category_rows:
        for text, colspan, start in parsed:
            if not text or start == 0:
                continue
            # Skip cells already captured as categories
            if start in position_texts:
                continue
            # Skip cells inside a category span
            inside_cat = False
            for cat_pos in sorted_positions:
                cat_end = cat_pos + position_colspans[cat_pos]
                if cat_pos <= start < cat_end:
                    inside_cat = True
                    break
            if inside_cat:
                continue
            clean_text = re.sub(r"<[Bb][Rr]\s*/?>", " ", text).strip()
            clean_text = re.sub(r"\s+", " ", clean_text)
            if clean_text:
                orphan_headers.append((clean_text, start))

    num_categories = len(categories)
    if num_categories == 0 and not orphan_headers:
        # No categories - just column headers
        header_layers = [[""] + column_headers_list]
        return header_layers, header_row_count

    # When there are orphan headers alongside categories, build a
    # combined position-ordered structure: orphan headers appear as
    # independent leaf columns (1 column each) and categories expand
    # to hold their sub-headers from year_rows.
    if orphan_headers and num_categories > 0:
        # Build a unified position list: each entry is either
        # ("orphan", text, start) or ("cat", name, start, colspan)
        unified: list = []
        for text, pos in orphan_headers:
            unified.append(("orphan", text, pos, 0))
        for cat_idx, cat_name in enumerate(categories):
            cat_pos = sorted_positions[cat_idx]
            cat_cs = position_colspans[cat_pos]
            unified.append(("cat", cat_name, cat_pos, cat_cs))
        unified.sort(key=lambda x: x[2])  # sort by start position

        cat_row = [""]
        header_row = [""]
        header_idx = 0

        for entry in unified:
            kind = entry[0]
            if kind == "orphan":
                orphan_text = entry[1]
                # Orphan headers are independent leaf columns —
                # they appear directly in the header row with empty
                # category text above.
                cat_row.append("")
                header_row.append(orphan_text)
            else:
                cat_name = entry[1]
                cat_pos = entry[2]
                cat_cs = entry[3]
                cat_end = cat_pos + cat_cs

                # Collect year headers whose positions fall within
                # this category's column range.
                sub_hdrs = []
                for hi in range(num_headers):
                    if column_headers_positions:
                        hdr_pos = column_headers_positions[hi]
                    else:
                        break
                    if cat_pos <= hdr_pos < cat_end:
                        sub_hdrs.append(column_headers_list[hi])

                if not sub_hdrs:
                    cat_row.append(cat_name)
                    header_row.append("")
                else:
                    cat_row.append(cat_name)
                    for _ in range(len(sub_hdrs) - 1):
                        cat_row.append("")
                    for sh in sub_hdrs:
                        header_row.append(sh)

        header_layers = [cat_row, header_row]

        return header_layers, header_row_count

    # Distribute column headers across categories
    # Use position-based matching when position info is available,
    # otherwise fall back to even distribution
    cat_row = [""]  # Start with label column
    header_row = [""]  # Start with label column

    if column_headers_positions and len(column_headers_positions) == num_headers:
        # Position-based distribution: match headers to categories
        # by checking which headers fall within each category's column range
        header_idx = 0

        # These are independent data columns (like unit-of-measure)
        # that don't belong under any period category.
        first_cat_pos = sorted_positions[0] if sorted_positions else 0
        while (
            header_idx < num_headers
            and column_headers_positions[header_idx] < first_cat_pos
        ):
            cat_row.append("")
            header_row.append(column_headers_list[header_idx])
            header_idx += 1

        for cat_idx, cat_name in enumerate(categories):
            cat_pos = sorted_positions[cat_idx]
            cat_cs = position_colspans[cat_pos]
            cat_end = cat_pos + cat_cs

            # Consume any gap/orphan headers that fall between the
            # previous category's end and this category's start.
            while (
                header_idx < num_headers
                and column_headers_positions[header_idx] < cat_pos
            ):
                cat_row.append("")
                header_row.append(column_headers_list[header_idx])
                header_idx += 1

            # Collect headers whose positions fall within [cat_pos, cat_end)
            start_idx = header_idx
            while header_idx < num_headers:
                hdr_pos = column_headers_positions[header_idx]
                if cat_pos <= hdr_pos < cat_end:
                    header_idx += 1
                else:
                    break

            count = header_idx - start_idx
            if count == 0:
                # Category has no sub-headers; add a single empty slot
                cat_row.append(cat_name)
                header_row.append("")
            else:
                cat_row.append(cat_name)
                for _ in range(count - 1):
                    cat_row.append("")

                for i in range(count):
                    idx = start_idx + i
                    if idx < len(column_headers_list):
                        header_row.append(column_headers_list[idx])
                    else:
                        header_row.append("")

        # Append any remaining unmatched headers
        while header_idx < num_headers:
            cat_row.append("")
            header_row.append(column_headers_list[header_idx])
            header_idx += 1
    else:
        # Fallback: even distribution when positions not available
        headers_per_category = (
            num_headers // num_categories if num_categories else num_headers
        )
        if headers_per_category == 0:
            headers_per_category = 1

        header_idx = 0
        for cat_name in categories:
            cat_row.append(cat_name)
            for _ in range(headers_per_category - 1):
                cat_row.append("")
            for i in range(headers_per_category):
                if header_idx < len(column_headers_list):
                    header_row.append(column_headers_list[header_idx])
                    header_idx += 1
                else:
                    header_row.append("")

    header_layers = [cat_row, header_row]

    return header_layers, header_row_count