def convert_table(table, base_url: str = "") -> str:
    """Convert HTML table to markdown table or text.

    Uses a single classification to determine table type:
    - BULLET: Tables with bullet chars in first column → bullet list
    - FOOTNOTE: Tables with (1), (a), * markers → "marker text" format
    - HEADER: Single-cell tables with section titles → markdown header
    - LAYOUT: Tables with multi-line content cells → section headers + bullet lists
    - DATA: Everything else → markdown table (the default)
    """
    # ── Chart-legend detection ──────────────────────────────────────
    # SEC filings embed bar / pie charts as <img> tags with adjacent
    # HTML tables that use tiny coloured cells as colour swatches
    # paired with label text (font-family: 'Gotham Narrow Book' /
    # similar, font-size ~5pt, rows of height 3pt).  The standard
    # table converter turns these into useless single-column markdown
    # tables.  Detect them early and emit a compact inline legend.
    legend = _extract_chart_legend(table)
    if legend is not None:
        return legend

    # Classify the table
    table_type = _classify_table(table)

    if table_type == "BULLET":
        result = _extract_bullet_list(table)
        if result:
            return result

    elif table_type == "FOOTNOTE":
        result = _extract_footnote_text(table)
        if result:
            return result

    elif table_type == "HEADER":
        result = _extract_header_text(table)
        if result:
            return result

    # For LAYOUT-classified tables (or unhandled types), try layout conversion.
    # Skip for DATA tables — they should always go through the data-table path.
    if table_type != "DATA":
        layout_result = _convert_layout_table(table, base_url)
        if layout_result:
            return layout_result

    # Default: process as data table (markdown table format)
    rows = table.find_all("tr")
    if not rows:
        return ""

    # Shared state: when year sub-headers start at position 0 (label
    # column), build_column_headers_from_colspan computes the offset
    # needed to align year positions with data-column positions.  The
    # semantic extraction code reads this to apply the same shift.
    _year_pos_shift = [0]  # mutable container so nested functions can write

    # First pass: Extract all rows WITHOUT merge/shift
    # We need to identify $ positions across all rows first
    raw_extracted_rows = []
    raw_extracted_colspans = []
    raw_row_has_th = []  # Track whether each row has <th> elements

    # Track grid positions occupied by cells with rowspan > 1 from
    # earlier rows.  Maps grid_col -> remaining row count.
    _rowspan_grid: dict[int, int] = {}

    for row in rows:
        cells = row.find_all(["td", "th"])
        row_data: list[str] = []
        row_with_colspan: list[tuple[str, int]] = []  # (text, colspan) pairs
        has_th = any(cell.name == "th" for cell in cells)

        grid_col = 0
        cell_idx = 0

        while cell_idx < len(cells):
            # Insert empty placeholders for positions occupied by
            # rowspan from earlier rows before placing the current cell.
            while grid_col in _rowspan_grid:
                row_data.append("")
                row_with_colspan.append(("", 1))
                grid_col += 1

            cell = cells[cell_idx]

            # Check for id attribute on cell - emit anchor if present
            cell_id = cell.get("id")
            anchor_prefix = ""
            if cell_id:
                anchor_prefix = f'<a id="{cell_id}"></a>'

            # For table cells, extract text while preserving links
            # but without the full recursive processing that introduces newlines
            text = _extract_cell_text(cell, base_url)

            # Clean up text - remove zero-width spaces and normalize whitespace
            text = text.replace("\u200b", "")
            text = text.replace("\xa0", " ")  # Non-breaking space
            text = re.sub(r"\s+", " ", text)
            text = text.strip()
            text = text.replace("|", "\\|")  # Escape pipes
            # Prepend anchor if cell had an id
            if anchor_prefix:
                text = anchor_prefix + text

            # Handle colspan and rowspan
            colspan = int(cell.get("colspan", 1) or 1)
            rowspan = int(cell.get("rowspan", 1) or 1)

            row_data.append(text)
            row_with_colspan.append((text, colspan))

            # Register this cell's grid positions for future rows
            if rowspan > 1:
                for _c in range(colspan):
                    _rowspan_grid[grid_col + _c] = rowspan

            for _ in range(colspan - 1):
                row_data.append("")

            grid_col += colspan
            cell_idx += 1

        # Fill any trailing positions still occupied by rowspan
        while grid_col in _rowspan_grid:
            row_data.append("")
            row_with_colspan.append(("", 1))
            grid_col += 1

        raw_extracted_rows.append(row_data)
        raw_extracted_colspans.append(row_with_colspan)
        raw_row_has_th.append(has_th)

        # Decrement rowspan counts; drop positions that have expired.
        _rowspan_grid = {pos: rem - 1 for pos, rem in _rowspan_grid.items() if rem > 1}

    # Identify positions that have currency prefixes ($, €, £) in ANY row.
    # These are the only positions where "empty + numeric" shift should apply.
    _CURRENCY_PREFIXES = {
        "$",
        "$(",
        "($",
        "$-",
        "€",
        "€(",
        "(€",
        "€-",
        "£",
        "£(",
        "(£",
        "£-",
    }
    dollar_positions = set()
    for row_data in raw_extracted_rows:
        for i, cell in enumerate(row_data):
            cell_stripped = strip_all(cell)
            if cell_stripped in _CURRENCY_PREFIXES:
                dollar_positions.add(i)

    # Extract all rows, preserving colspan info for headers
    data = []
    raw_rows_with_colspan = []  # For header detection - stores (text, colspan) pairs
    row_has_th_flags = []  # Track which rows have <th> elements
    for row_idx, (row_data, row_with_colspan, has_th) in enumerate(
        zip(raw_extracted_rows, raw_extracted_colspans, raw_row_has_th)
    ):
        # Merge currency prefix cells with their following value cells.
        # SEC tables often have $ in one cell and the number in the next.
        # 20-F filings frequently use € with colspan=3, placing the number
        # up to 3 positions away after empty expansion cells.
        merged_row = []
        merged_row_with_colspan = []
        i = 0
        while i < len(row_data):
            cell = strip_all(row_data[i])
            # Check if this is a currency prefix cell ($, €, £, etc.)
            if cell in _CURRENCY_PREFIXES and i + 1 < len(row_data):
                # Look ahead up to 3 positions for the number
                # (currency cell may have colspan>1 producing empty gaps)
                _num_re = re.compile(r"^\(?\s*[\d,]+\.?\d*\s*\)?%?$")
                _found_offset = None
                for _look in range(1, min(4, len(row_data) - i)):
                    _ahead = strip_all(row_data[i + _look])
                    if _ahead and _num_re.match(_ahead):
                        _found_offset = _look
                        break
                    if _ahead:  # non-empty non-numeric → stop
                        break
                if _found_offset is not None:
                    merged_val = cell + strip_all(row_data[i + _found_offset])
                    merged_row.append(merged_val)
                    # Add empty placeholders for all consumed cells
                    for _ in range(_found_offset):
                        merged_row.append("")
                    # Preserve colspan tracking for all consumed cells
                    for j in range(_found_offset + 1):
                        if i + j < len(row_with_colspan):
                            merged_row_with_colspan.append(row_with_colspan[i + j])
                    i += _found_offset + 1
                    continue
            # Handle rows WITHOUT currency prefix: empty cell followed by
            # a numeric value.  Secondary data rows may omit the currency
            # symbol shown on the first row.  Shift the value to the
            # currency position to keep alignment.  Also use look-ahead
            # (up to 3 cells) for €-style tables with colspan>1 gaps.
            elif cell == "" and i + 1 < len(row_data) and i in dollar_positions:
                _num_re2 = re.compile(r"^\(?\s*[\d,]+\.?\d*\s*\)?%?$")
                _found_offset2 = None
                for _look2 in range(1, min(4, len(row_data) - i)):
                    _ahead2 = strip_all(row_data[i + _look2])
                    if _ahead2 and _num_re2.match(_ahead2):
                        _found_offset2 = _look2
                        break
                    if _ahead2:
                        break
                if _found_offset2 is not None:
                    merged_row.append(strip_all(row_data[i + _found_offset2]))
                    for _ in range(_found_offset2):
                        merged_row.append("")
                    for j in range(_found_offset2 + 1):
                        if i + j < len(row_with_colspan):
                            merged_row_with_colspan.append(row_with_colspan[i + j])
                    i += _found_offset2 + 1
                    continue
            merged_row.append(row_data[i])
            if i < len(row_with_colspan):
                merged_row_with_colspan.append(row_with_colspan[i])
            i += 1

        row_data = merged_row  # noqa
        row_with_colspan = merged_row_with_colspan  # noqa

        # Merge footnote cells with the ROW LABEL (first non-empty cell)
        # SEC tables have footnote markers like <sup>12</sup> in their own cells
        # These belong on the label, not on data values
        footnote_merged_row = []
        collected_footnotes = []
        label_index = -1  # Track which cell is the row label

        for i, cell_text in enumerate(row_data):
            # Check if this cell is ONLY a superscript footnote
            if re.match(r"^\s*<sup>\d{1,3}</sup>\s*$", cell_text):
                # Collect footnotes to append to label later
                collected_footnotes.append(cell_text)
            else:
                footnote_merged_row.append(cell_text)
                # First non-empty cell is the label
                if label_index == -1 and cell_text.strip():
                    label_index = len(footnote_merged_row) - 1

        # Append all collected footnotes to the row label
        if collected_footnotes and label_index >= 0:
            footnote_merged_row[label_index] = footnote_merged_row[
                label_index
            ] + "".join(collected_footnotes)

        row_data = footnote_merged_row  # noqa

        if any(row_data):  # Skip empty rows
            data.append(row_data)
            raw_rows_with_colspan.append(row_with_colspan)
            row_has_th_flags.append(has_th)

    if not data:
        return ""

    # Filter out page footer tables
    if len(data) <= 2:
        non_empty = [c for c in data[0] if c.strip()]
        if len(non_empty) == 2:
            first_cell = non_empty[0].strip()
            second_cell = non_empty[1].strip()
            first_lower = first_cell.lower()
            second_lower = second_cell.lower()
            form_keywords = ["form 10-", "10-k", "10-q", "annual report"]
            if (
                first_cell.isdigit() and any(kw in second_lower for kw in form_keywords)
            ) or (
                second_cell.isdigit() and any(kw in first_lower for kw in form_keywords)
            ):
                return ""  # Skip page footer

    # Check if this is a section header table (single cell with TOC anchor)
    # Header like: <td id="toc..."><div style="font-weight:bold">Section Title</div></td>
    if len(data) == 1 and len([c for c in data[0] if c.strip()]) == 1:
        cell_text = [c for c in data[0] if c.strip()][0]
        # Check if it has a TOC anchor
        if '<a id="toc' in cell_text or '<a id="TOC' in cell_text:
            # Extract the text after the anchor
            text_match = re.search(r"</a>(.*)", cell_text)
            anchor_match = re.search(r'(<a id="[^"]+"></a>)', cell_text)
            if text_match and anchor_match:
                anchor = anchor_match.group(1)
                header_text = text_match.group(1).strip()
                if header_text:
                    return f"\n\n{anchor}\n\n### {header_text}\n\n"

    # Check if this is a bullet-list layout table
    # Must have actual bullet characters, not just empty cells
    is_bullet_list = False
    bullet_items = []
    for row in data:
        non_empty = [c for c in row if c.strip()]
        if len(non_empty) == 2 and non_empty[0] in BULLET_CHARS:
            # Actual bullet + text pattern
            bullet_items.append(non_empty[1])
            is_bullet_list = True
        elif len(non_empty) == 1 and is_bullet_list:
            # Continuation of bullet list (single items after we've seen bullets)
            bullet_items.append(non_empty[0])
        elif len(non_empty) >= 1 and not is_bullet_list:
            # Single row with content but not a bullet pattern
            # Join all non-empty cells as text (preserves both image and text)
            if len(data) == 1:
                return " ".join(non_empty)
            break
        else:
            is_bullet_list = False
            break

    if is_bullet_list and bullet_items:
        return "\n".join(f"- {item}" for item in bullet_items)

    # Normalize column count
    max_cols = max(len(row) for row in data)
    for row in data:
        while len(row) < max_cols:
            row.append("")

    # Clean up financial table formatting

    data = clean_table_cells(data)

    # Normalize financial values to compact format.
    # SEC filings use spacer elements between $ signs, parentheses, and
    # numbers, producing inconsistent formats like "$ 1,787" vs "$1,787"
    # or "( 135 )" vs "(135)".  Normalize everything to compact form.
    data = _normalize_financial_rows(data)

    # Merge consecutive rows that contain split text (e.g., "(in millions, except per" + "share amounts)")
    # This happens when HTML has multi-line text split across separate TR elements

    data, raw_rows_with_colspan = merge_split_rows(data, raw_rows_with_colspan)

    # Merge cells that contain split values within each row
    # Old SEC HTML often splits negative numbers like "(306" and ")" across cells
    # and puts footnote markers like "(1)" in separate cells

    data = merge_split_cells(data)

    # Normalize column count after cleaning
    if data:
        max_cols = max(len(row) for row in data)
        for row in data:
            while len(row) < max_cols:
                row.append("")

    # Remove columns that are completely empty

    # Step 1: Extract period headers from header rows

    # Step 2: Parse each row semantically - first text is label, numbers are values

    # Detect multi-level headers directly from DATA (not raw_rows_with_colspan)
    # This handles SEC tables where categories are stacked vertically:
    #   Row: EQUIPMENT | FINANCIAL | | | ...
    #   Row: OPERATIONS | SERVICES | ELIMINATIONS | CONSOLIDATED | ...
    #   Row: 2025 | 2024 | 2023 | 2025 | 2024 | 2023 | ...

    # Try to detect multi-index headers from data
    multiindex_result = detect_and_merge_multiindex_headers(data)

    if multiindex_result[0] and len(multiindex_result[0]) >= 1:
        header_layers, data_start_idx, num_periods = multiindex_result
        is_financial_periods = True
        header_row_count = data_start_idx
    else:
        # Fall back to original approach
        header_layers, extracted_header_count = extract_periods_from_rows(
            raw_rows_with_colspan, row_has_th_flags, _year_pos_shift
        )

        num_periods = 0

        if header_layers:
            # Count columns that have content in ANY header layer, but
            # collapse adjacent positions with identical composite text
            # (from colspan expansion).  E.g., "2025" at positions 3,4,5
            # from a cs=3 header counts as ONE period, not three.
            max_cols = max(len(layer) for layer in header_layers)
            num_periods = 0
            prev_key = None
            for col_idx in range(1, max_cols):  # Skip first col (label)
                key_parts = []
                has_content = False
                for layer in header_layers:
                    text = layer[col_idx].strip() if col_idx < len(layer) else ""
                    key_parts.append(text)
                    if text:
                        has_content = True
                if has_content:
                    key = "|".join(key_parts)
                    if key != prev_key:
                        num_periods += 1
                    prev_key = key
                else:
                    prev_key = None  # Reset on empty columns

            # When all header layers have the same size they are already
            # compact (from the flat-header / multi-category-row path).
            # Empty trailing columns still represent real data columns
            # (e.g., a total column with no header text), so trust the
            # layer size as the minimum column count.
            layer_sizes = set(len(hl) for hl in header_layers)

            if len(layer_sizes) == 1:
                layers_cols = layer_sizes.pop() - 1  # subtract label col
                num_periods = max(num_periods, layers_cols)

        # Check if headers are financial periods (years, dates, "months ended",
        # or maturity-bucket labels like "0 - 6 Months" / "1 - 5 Years")
        is_financial_periods = False

        if header_layers:
            for layer in header_layers:
                for h in layer:
                    if re.search(r"\b(19|20)\d{2}\b", h):  # Has a year
                        is_financial_periods = True
                        break
                    if re.search(
                        r"(months?\s+ended|year\s+ended|quarter|as\s+of)", h, re.I
                    ):
                        is_financial_periods = True
                        break
                    # Maturity-bucket labels: "0 - 6 Months", "1 - 5 Years",
                    # "10 Years or Greater", "Less than 1 Year", etc.
                    if re.search(
                        r"\d+\s*[-\u2013\u2014]\s*\d+\s*(months?|years?)"
                        r"|\d+\s+(months?|years?)(\s+or\s+(greater|more|less))?"
                        r"|less\s+than\s+\d+\s+(months?|years?)",
                        h,
                        re.I,
                    ):
                        is_financial_periods = True
                        break

                if is_financial_periods:
                    break

        # Use extracted_header_count if available
        header_row_count = extracted_header_count

    # These need special handling to merge headers and align columns

    # Try equity statement processing first
    if is_equity_statement_table(data):
        equity_result, equity_header_count = process_equity_statement_table(
            data, raw_rows_with_colspan
        )
        if equity_result:
            data = equity_result
            num_header_rows = equity_header_count
            # Skip the usual processing - go directly to markdown output
            if data and data[0]:
                max_cols = max(len(row) for row in data) if data else 0
                lines = []
                for i, row in enumerate(data):
                    while len(row) < max_cols:
                        row.append("")
                    clean_row = []
                    for cell in row:
                        clean_cell = re.sub(r"[\r\n]+", " ", cell)
                        # Remove <br>/<BR> tags from header cells (first few rows)
                        # num_header_rows is equity_header_count here
                        if i < max(num_header_rows, 2):
                            clean_cell = re.sub(r"<[Bb][Rr]\s*/?>", " ", clean_cell)
                        clean_cell = re.sub(r" +", " ", clean_cell).strip()
                        clean_row.append(clean_cell)
                    line = "| " + " | ".join(clean_row) + " |"
                    lines.append(line)
                    # Separator after FIRST row only (markdown requirement)
                    if i == 0:
                        lines.append("|" + "|".join(["---"] * max_cols) + "|")
                return "\n".join(lines)

    # Build output table
    new_data = []

    # Helper to check if a row from data array is a header/title row (should be skipped)
    has_meaningful_headers = False
    has_financial_header_terms = False
    if header_layers:
        all_header_text = " ".join(h for layer in header_layers for h in layer)

        for layer in header_layers:
            # Check for multi-word headers that indicate merged vertical labels
            for _h in layer:
                h = _h.strip()
                # Multi-word headers (e.g., "Retail Notes & Financing Leases")
                if h and len(h.split()) >= 2 and not re.match(r"^(19|20)\d{2}$", h):
                    has_meaningful_headers = True
                    break
            if has_meaningful_headers:
                break

        # Check for financial terms in headers that indicate structured financial table
        # These terms indicate the table should be parsed semantically even without years
        financial_header_terms = [
            r"\bshares?\b",
            r"\bprice\b",
            r"\bvalue\b",
            r"\bterm\b",
            r"\bexercise\b",
            r"\bgranted?\b",
            r"\bvested\b",
            r"\bforfeited?\b",
            r"\b(?:thousands?|millions?|billions?)\b",
            r"\bper\s+share\b",
            r"\baggregate\b",
            r"\bintrinsic\b",
            r"\bcontractual\b",
            r"\bremaining\b",
            r"\bweighted[-\s]?average\b",
            r"\bexercisable\b",
            r"\bAmount\b",
            r"\bCredit\b",
            r"\bDebit\b",
            r"\bBalance\b",
            r"\bReceivables?\b",
            r"\bLeases?\b",
            r"\bFinancing\b",
            r"\bWholesale\b",
            # Maturity / time-duration bucket labels
            r"\bmonths?\b",
            r"\byears?\b",
            r"\bor\s+greater\b",
            r"\bmaturity\b",
        ]
        has_financial_header_terms = any(
            re.search(term, all_header_text, re.I) for term in financial_header_terms
        )

    has_mixed_headers = False

    if header_layers and len(header_layers) == 1:
        # Single header row - check if it mixes years with non-year columns.
        # "Mixed" means the non-year columns OUTNUMBER the year/year-range
        # columns, implying the headers are different dimensions (e.g.,
        # "2024 | 2023 | % Change | Useful Lives") rather than a year-period
        # table with a summary column ("2008 | 2009-2010 | ... | Total").
        last_layer = header_layers[-1]
        year_cols: int = 0
        non_year_cols: int = 0

        for _h in last_layer[1:]:  # Skip label column
            h = _h.strip()
            if not h:
                continue
            if re.search(r"\b(19|20)\d{2}\b", h):
                year_cols += 1
            else:
                non_year_cols += 1

        # Mixed only when non-year columns are the majority, or there are NO
        # year columns at all AND the headers don't form a cohesive maturity-
        # bucket set (e.g. "0 - 6 Months", "1 - 5 Years", "Total").
        # Maturity-bucket tables look like year-range tables but use time
        # durations instead of calendar years — they are NOT truly mixed.
        _maturity_bucket_re = re.compile(
            r"^\s*("
            r"\d+\s*[-\u2013\u2014]\s*(\d+|\w+)\s*(months?|years?)"
            r"|\d+\s+(months?|years?)(\s+or\s+(greater|more|less))?"
            r"|less\s+than\s+\d+"
            r"|or\s+(greater|more|less)"
            r"|n/?a"
            r"|total"
            r"|thereafter"
            r")\s*$",
            re.I,
        )
        if year_cols == 0:
            # All non-empty, non-label headers are maturity buckets → not mixed
            _all_maturity = all(
                _maturity_bucket_re.match(h) for h in last_layer[1:] if h.strip()
            )
            if not _all_maturity:
                has_mixed_headers = True
        elif non_year_cols > year_cols:
            has_mixed_headers = True

    use_semantic_parsing = (
        is_financial_periods and header_layers and not has_mixed_headers
    )

    if (
        not use_semantic_parsing
        and header_layers
        and has_meaningful_headers
        and has_financial_header_terms
        and not has_mixed_headers
    ):
        # Treat merged vertical headers with financial terms as financial tables
        use_semantic_parsing = True

    # Guard: verify num_periods matches the actual data width.
    # Complex multi-index headers (e.g., "Economic value sensitivity" spanning
    # date sub-headers spanning country sub-sub-headers) can cause the header
    # detection to undercount periods.  When data rows consistently have more
    # non-empty values than num_periods, the header structure is wrong and we
    # must fall back to positional (non-semantic) rendering.
    if use_semantic_parsing and num_periods > 0 and header_row_count < len(data):
        _val_re = re.compile(
            r"^[+\-]?[\$\u20ac]?\s*\(?[\$\u20ac]?\s*[\d,]+\.?\d*\s*\)?\s*[*%]*(pts)?$"
        )
        _dash_vals = {
            "\u2014",
            "\u2013",
            "-",
            "$\u2014",
            "$\u2013",
            "$-",
            "\u20ac\u2014",
            "\u20ac\u2013",
            "\u20ac-",
            "N/A",
            "n/a",
            "NM",
            "nm",
        }
        for _dr in data[header_row_count:]:
            _n = sum(
                1
                for c in _dr[1:]
                if c.strip() and (_val_re.match(c.strip()) or c.strip() in _dash_vals)
            )
            if _n > num_periods * 2:
                use_semantic_parsing = False
                break

    if use_semantic_parsing:
        # For multi-level headers, derive column positions from year cells
        # in the expanded data array. This enables position-aware extraction
        # for sparse data rows (where values have gaps between columns).
        header_col_positions = None

        if header_layers and len(header_layers) >= 2:
            year_positions = []
            for row_idx in range(min(header_row_count, len(data))):
                for col_idx, cell in enumerate(data[row_idx]):
                    cell_clean = cell.strip().strip("\u200b").strip()
                    # Strip footnote markers
                    cell_stripped = re.sub(r"[*†‡§+]+$", "", cell_clean)

                    if (
                        cell_stripped
                        and re.match(r"^(19|20)\d{2}$", cell_stripped)
                        and col_idx not in year_positions
                    ):
                        year_positions.append(col_idx)

            year_positions.sort()

            if len(year_positions) == num_periods and num_periods > 0:
                # When year headers start at column 0 (label column),
                # they are offset from data values.  Apply the same shift
                # that was computed during header extraction so positions
                # align with actual data columns.
                if year_positions[0] == 0 and _year_pos_shift[0] > 0:
                    year_positions = [p + _year_pos_shift[0] for p in year_positions]
                header_col_positions = year_positions

            # When year_positions alone don't cover all periods (e.g.,
            # tables with "% Change" or "Basis Point Change" columns
            # alongside date columns), augment with positions of other
            # non-empty header texts from the header data rows.  Exclude
            # category texts (from Layer 0) and financial data values.
            if (
                not header_col_positions
                and year_positions
                and len(year_positions) < num_periods
                and num_periods > 0
            ):
                category_texts_set: set[str] = set()
                if header_layers:
                    for _h in header_layers[0]:
                        _ht = _h.strip()
                        if _ht:
                            category_texts_set.add(_ht)

                all_leaf_positions: set[int] = set(year_positions)
                for row_idx in range(min(header_row_count, len(data))):
                    for col_idx, cell in enumerate(data[row_idx]):
                        if col_idx == 0 or col_idx in all_leaf_positions:
                            continue
                        cell_clean = cell.strip().strip("\u200b").strip()
                        cell_stripped = re.sub(r"[*†‡§+]+$", "", cell_clean)
                        if not cell_stripped:
                            continue
                        # Skip years (already collected)
                        if re.match(r"^(19|20)\d{2}$", cell_stripped):
                            continue
                        # Skip financial data values
                        if re.match(
                            r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$",
                            cell_stripped,
                        ):
                            continue
                        # Skip category header texts (from colspan expansion)
                        if cell_stripped in category_texts_set:
                            continue
                        # Skip descriptor text in parentheses
                        if cell_stripped.startswith("(") and re.search(
                            r"(million|except|thousand|billion|percent)",
                            cell_stripped,
                            re.I,
                        ):
                            continue
                        all_leaf_positions.add(col_idx)

                sorted_all = sorted(all_leaf_positions)
                if len(sorted_all) == num_periods:
                    header_col_positions = sorted_all

            # For tables with text sub-headers (no year values),
            # dollar signs mark the start of each data column
            if not header_col_positions and dollar_positions:
                sorted_dollar = sorted(dollar_positions)

                if len(sorted_dollar) == num_periods and num_periods > 0:
                    header_col_positions = sorted_dollar

            if not header_col_positions and header_layers:
                # Build a list of (col_idx_in_layer, text, layer_idx) for all
                # non-empty header positions, then deduplicate by column index.
                all_header_entries = []  # (col_pos, text, layer_idx)

                for li, layer in enumerate(header_layers):
                    for col_pos in range(1, len(layer)):
                        h = layer[col_pos].strip()

                        if h:
                            all_header_entries.append((col_pos, h, li))

                # Deduplicate
                col_to_text: dict = {}

                for col_pos, h, li in all_header_entries:
                    if col_pos not in col_to_text or li > col_to_text[col_pos][1]:
                        col_to_text[col_pos] = (h, li)

                sub_texts = [col_to_text[cp][0] for cp in sorted(col_to_text.keys())]

                if len(sub_texts) == num_periods and num_periods > 0:
                    found_positions: list[int] = []
                    used_cols: set[int] = set()

                    for target in sub_texts:
                        matched = False
                        for row_idx in range(min(header_row_count, len(data))):
                            for col_idx, cell in enumerate(data[row_idx]):
                                if col_idx in used_cols:
                                    continue

                                if cell.strip() == target:
                                    found_positions.append(col_idx)
                                    used_cols.add(col_idx)
                                    matched = True
                                    break

                            if matched:
                                break

                    if len(found_positions) == num_periods:
                        header_col_positions = sorted(found_positions)

        # Single-layer header fallback: find where each unique header text
        # first appears in the raw (colspan-expanded) data header rows.
        # E.g., header_layers=[['', '2025', '2024', '% Change']] and the
        # raw data row is ['', '', '2025', '2025', '', '2024', '2024', '',
        # '% Change', ''].  We need header_col_positions=[2, 5, 8] so the
        # position-aware extraction maps data cells to correct columns.
        if not header_col_positions and header_layers and len(header_layers) == 1:
            unique_headers = [h for h in header_layers[0][1:] if h.strip()]
            if len(unique_headers) == num_periods and num_periods > 0:
                found_positions = []
                used_cols = set()
                for target in unique_headers:
                    for row_idx in range(min(header_row_count, len(data))):
                        matched = False
                        for col_idx, cell in enumerate(data[row_idx]):
                            if col_idx in used_cols:
                                continue
                            if cell.strip() == target:
                                found_positions.append(col_idx)
                                used_cols.add(col_idx)
                                matched = True
                                break
                        if matched:
                            break
                if len(found_positions) == num_periods:
                    header_col_positions = found_positions

        if header_layers:
            for layer in header_layers:
                if len(layer) == num_periods + 1:
                    new_data.append(layer[:])
                    continue

                # Pad on the right to match the expected column count rather than collapsing.
                if len(layer) <= num_periods + 1:
                    padded = layer[:] + [""] * (num_periods + 1 - len(layer))
                    new_data.append(padded[: num_periods + 1])
                    continue

                # Collapse adjacent identical texts from colspan expansion.
                # E.g., ['', '', '', '2025', '2025', '2025', '', '', '',
                #         '2024', '2024', '2024', ...]
                # becomes ['', '2025', '2024', '2023']
                collapsed = []
                prev_text = None
                for idx, text in enumerate(layer):
                    t = text.strip()

                    if idx == 0:
                        # Always keep the label column as-is
                        collapsed.append(text)
                        prev_text = None
                        continue

                    if t:
                        if t != prev_text:
                            collapsed.append(text)
                        prev_text = t
                    else:
                        prev_text = None  # Reset on empty

                # Ensure it has the right number of columns
                while len(collapsed) < num_periods + 1:
                    collapsed.append("")
                new_data.append(collapsed[: num_periods + 1])

        # Process data rows - use header_row_count to skip header rows
        # Use a two-pass approach: first extract values into *groups*
        # per header range, then flatten.  This correctly interleaves
        # sub-column values (e.g. absolute change + percentage under a
        # single "2025 vs. 2024" header) instead of appending overflows
        # to the end.
        _extracted_rows: list[tuple] = []
        _has_sub_columns = False
        _num_header_entries = len(new_data)  # header rows already added

        for i, row in enumerate(data):
            # Skip rows before data starts (headers already extracted)
            if i < header_row_count:
                continue

            # Also skip any remaining header-like rows by content
            if is_data_row_header(row):
                continue

            if header_col_positions:
                # Position-aware extraction: map data cells to headers
                # by checking which header column range each cell falls in
                ranges = []

                for hi, pos in enumerate(header_col_positions):
                    end = (
                        header_col_positions[hi + 1]
                        if hi + 1 < len(header_col_positions)
                        else len(row)
                    )
                    ranges.append((pos, end))

                label_parts = []
                value_groups: list[list[str]] = [[] for _ in range(num_periods)]

                for col_idx, cell_text in enumerate(row):
                    cell_clean = cell_text.strip().strip("\u200b").strip()

                    if not cell_clean or cell_clean in ("$", "\u20ac"):
                        continue
                    # Before first header position = label column
                    if col_idx < header_col_positions[0]:
                        label_parts.append(cell_clean)
                        continue

                    # Find which header range this cell falls into
                    for hi, (start, end) in enumerate(ranges):
                        if start <= col_idx < end:
                            # Numeric/dash values go as data
                            if re.match(
                                r"^[+\-]?[\$\u20ac]?\s*\(?[\$\u20ac]?\s*[\d,]+\.?\d*\s*\)?\s*[*%]*(pts)?$",
                                cell_clean,
                            ) or cell_clean in (
                                "\u2014",
                                "\u2013",
                                "-",
                                "$\u2014",
                                "$\u2013",
                                "$-",
                                "$ \u2014",
                                "$ \u2013",
                                "$ -",
                                "\u20ac\u2014",
                                "\u20ac\u2013",
                                "\u20ac-",
                                "\u2014%",
                                "\u2013%",
                                "-%",
                                "\u2014 %",
                                "\u2013 %",
                                "- %",
                                "N/A",
                                "n/a",
                                "NM",
                                "nm",
                            ):
                                value_groups[hi].append(cell_clean)
                                if len(value_groups[hi]) > 1:
                                    _has_sub_columns = True
                            elif (
                                re.match(
                                    r"^(bps?|pts?|pps?|x)$",
                                    cell_clean,
                                    re.I,
                                )
                                and value_groups[hi]
                            ):
                                # Unit suffix (e.g. "bps", "pts") that
                                # belongs to the preceding numeric value
                                # in the same header range — merge rather
                                # than creating a spurious extra column.
                                value_groups[hi][
                                    -1
                                ] = f"{value_groups[hi][-1]} {cell_clean}"
                            elif not label_parts:
                                # Non-numeric before any data = part of label
                                label_parts.append(cell_clean)
                            else:
                                value_groups[hi].append(cell_clean)
                                if len(value_groups[hi]) > 1:
                                    _has_sub_columns = True

                            break

                label = " ".join(label_parts) if label_parts else None
                _extracted_rows.append((label, value_groups))
            else:
                label, values = parse_row_semantic(row, num_periods)
                # Wrap each value as a single-element group
                _extracted_rows.append((label, [[v] if v else [] for v in values]))

        # Determine max sub-column count per period across all rows.
        _max_group_sizes = [1] * num_periods
        if _has_sub_columns:
            for _, groups in _extracted_rows:
                for hi in range(min(num_periods, len(groups))):
                    _max_group_sizes[hi] = max(_max_group_sizes[hi], len(groups[hi]))

        _actual_periods = sum(_max_group_sizes)

        # Flatten each row's value groups into a flat value list.
        for label, groups in _extracted_rows:
            if label is None and all(not g for g in groups):
                continue

            flat_values: list[str] = []
            for hi in range(num_periods):
                g = list(groups[hi]) if hi < len(groups) else []
                while len(g) < _max_group_sizes[hi]:
                    g.append("")
                flat_values.extend(g)

            while len(flat_values) < _actual_periods:
                flat_values.append("")

            new_data.append([label or ""] + flat_values)

        # Expand header layers if sub-columns were detected.
        if _has_sub_columns and _actual_periods > num_periods:
            for li in range(_num_header_entries):
                old_hdr = new_data[li]
                expanded = [old_hdr[0]]  # label column
                for hi in range(num_periods):
                    h = old_hdr[hi + 1] if hi + 1 < len(old_hdr) else ""
                    expanded.append(h)
                    for _ in range(_max_group_sizes[hi] - 1):
                        expanded.append("")
                while len(expanded) < _actual_periods + 1:
                    expanded.append("")
                new_data[li] = expanded
            num_periods = _actual_periods

        data = new_data
        num_header_rows = len(header_layers) if header_layers else 1

        # Re-align single-layer period headers to match actual data column
        # positions.  When a year header like "September 2025" (cs=6) spans
        # multiple physical data columns (e.g. amount + percentage), the
        # collapsed header row places it at col 1 while "December 2024" lands
        # at col 2 — even though the December data starts at col 3.
        # Fix: scan the first data row for dollar-prefixed values ($xxx) and
        # move each period name to the column where its period's $ amount sits.
        if (
            header_layers
            and len(header_layers) == 1
            and num_periods >= 2
            and len(header_layers[0]) == num_periods + 1
            and len(data) > num_header_rows
        ):
            _period_names = [h for h in header_layers[0][1:] if h.strip()]
            if len(_period_names) == num_periods:
                _dollar_cols: list = []
                for _drow in data[num_header_rows:]:
                    _positions = [
                        ci for ci, c in enumerate(_drow) if c and c.startswith("$")
                    ]
                    if len(_positions) == num_periods:
                        _dollar_cols = _positions
                        break
                if _dollar_cols and max(_dollar_cols) >= num_periods:
                    # Only realign if dollar cols are NOT already sequential
                    # from 1..num_periods (which would mean no change needed)
                    _expected = list(range(1, num_periods + 1))
                    if _dollar_cols != _expected:
                        _max_dc = max(len(r) for r in data)
                        _new_hdr = [""] * _max_dc
                        for _pi, _pos in enumerate(_dollar_cols):
                            if _pos < _max_dc:
                                _new_hdr[_pos] = _period_names[_pi]
                        data[0] = _new_hdr

    elif has_mixed_headers and header_layers:
        # Mixed-header table (has non-year columns like "Useful Lives")
        header_part = data[:header_row_count]
        if is_financial_periods:
            filtered_rows = [
                row for row in data[header_row_count:] if not is_data_row_header(row)
            ]
        else:
            filtered_rows = list(data[header_row_count:])
        data = header_part + filtered_rows

        # Check if this is a simple flat table
        if header_row_count == 1:
            data = remove_empty_columns(data)
            data = collapse_repeated_headers(data)
            num_header_rows = 1
        else:
            # Multi-row header structure with mixed headers.
            header_part = data[:header_row_count]
            data_rows_only = data[header_row_count:]

            actual_header_rows = []
            for row in header_part:
                non_empty = [c for c in row if c.strip()]

                if len(non_empty) >= 2:
                    # Multiple cells with content → column-defining header
                    actual_header_rows.append(row)

            if not actual_header_rows:
                # Fallback: use the last header row
                actual_header_rows = [header_part[-1]]

            combined = actual_header_rows + data_rows_only
            combined = remove_empty_columns(combined)
            combined = collapse_repeated_headers(combined)

            data = combined
            num_header_rows = len(actual_header_rows)
    else:
        # Non-financial table - filter out header-like rows from data portion
        if header_row_count > 0:
            header_part = data[:header_row_count]
            filtered_rows = [
                row for row in data[header_row_count:] if not is_data_row_header(row)
            ]
            data = header_part + filtered_rows
        data = remove_empty_columns(data)
        # This handles tables where header has colspan=2 but data only fills one position
        data = collapse_repeated_headers(data)
        num_header_rows = 0

    if not data or not data[0]:
        return ""

    max_cols = max(len(row) for row in data) if data else 0
    lines = []

    for i, row in enumerate(data):
        while len(row) < max_cols:
            row.append("")
        # Ensure no cell contains newlines
        clean_row = []

        for cell in row:
            # Replace any newlines with space
            clean_cell = re.sub(r"[\r\n]+", " ", cell)
            # Remove <br>/<BR> tags from header cells (first few rows)
            # This handles multi-row headers where row 1 also has column names
            if i < max(num_header_rows, 2):
                clean_cell = re.sub(r"<[Bb][Rr]\s*/?>", " ", clean_cell)
            # Collapse multiple spaces
            clean_cell = re.sub(r" +", " ", clean_cell).strip()
            clean_row.append(clean_cell)

        line = "| " + " | ".join(clean_row) + " |"
        lines.append(line)
        # Add separator after the first header row only — this is standard markdown.
        # Additional header layers (Layer 1, Layer 2...) render as normal rows below
        # the separator, acting as visual sub-headers.
        if i == 0:
            lines.append("|" + "|".join(["---"] * max_cols) + "|")

    return "\n".join(lines)