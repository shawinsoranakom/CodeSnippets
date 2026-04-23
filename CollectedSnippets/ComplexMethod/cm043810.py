def merge_vertical_headers(rows_with_cs, total_cols, row_has_th_flags=None):
        """Merge consecutive header rows that have text at same column positions.

        For tables like:
            Row 1: "Retail Notes"[cs=2] | "Revolving"[cs=2]
            Row 2: "& Financing"[cs=2] | "Charge"[cs=2] | "Wholesale"[cs=2]
            Row 3: "Leases"[cs=2] | "Accounts"[cs=2] | "Receivables"[cs=2] | "Total"[cs=2]

        Merges to: ["Retail Notes & Financing Leases", "Revolving Charge Accounts",
                   "Wholesale Receivables", "Total"]

        Args:
            rows_with_cs: List of rows with colspan info
            total_cols: Total number of columns in table
            row_has_th_flags: Optional list of booleans - if row has only <td> elements (no <th>),
                             it's definitely a data row, not a header row
        """
        if not rows_with_cs:
            return None, 0

        # Helper to check if text looks like a header (not data, not a year)
        def is_header_text(t):
            if not t:
                return False
            # Remove zero-width chars
            t = (
                t.replace("\u200b", "")
                .replace("\u200c", "")
                .replace("\u200d", "")
                .replace("\ufeff", "")
                .strip()
            )
            if not t:
                return False
            # Years are headers
            if re.match(r"^(19|20)\d{2}$", t):
                return True
            # Year-range labels like "2009 -", "2011 –", "2013-" are headers
            # (the trailing dash signals the start of a date range spanning the
            # child row, e.g. "2009 - 2010").
            if re.match(r"^(19|20)\d{2}\s*[\-\u2013\u2014]", t):
                return True
            # Data patterns - not headers
            if re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t):
                return False
            # Single punctuation - not a header
            if len(t) <= 1:
                return False
            # Numeric range labels like "0 - 6", "6 - 12", "1 - 5" are maturity
            # bucket column headers — they contain no letters but are clearly headers.
            if re.match(r"^\d+\s*[-\u2013\u2014]\s*\d+$", t):
                return True
            # Text with letters is likely a header
            return bool(re.search(r"[A-Za-z]", t))

        # Helper to check if row is a data row (has numeric values OR rating-like values)
        def is_data_row(row):
            col_pos = 0
            for text, cs in row:
                t = (
                    text.replace("\u200b", "")
                    .replace("\u200c", "")
                    .replace("\u200d", "")
                    .replace("\ufeff", "")
                    .strip()
                )
                if (
                    t
                    and re.match(r"^[\$]?\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", t)
                    and not re.match(r"^(19|20)\d{2}$", t)
                ):
                    # At position 0 (label column), a bare small number
                    # (1-3 digits with no financial formatting) may be a
                    # rendering artifact rather than a data value.
                    if col_pos == 0 and re.match(r"^\d{1,3}$", t):
                        col_pos += cs
                        continue
                    # Check if it's a year (years in header rows are ok)
                    return True
                # Also check for rating-like values (A+, A1, Prime-1, F1, Stable, etc.)
                # These are alphanumeric but short and look like data, not headers
                if t and len(t) <= 10:
                    # Short alphanumeric codes that are likely ratings/data
                    # Examples: A+, A1, Aa1, BBB+, Prime-1, F1, Stable, Positive, Negative
                    # IMPORTANT: Must end with a modifier (+/-/digit) to distinguish from words like "Tax"
                    if re.match(r"^[A-Z][a-z]{0,2}[+-][0-9]?$", t):  # A+, Aa+, Baa+
                        return True
                    if re.match(r"^[A-Z][a-z]{0,2}[0-9]$", t):  # A1, Aa1, Baa1
                        return True
                    if re.match(r"^[A-Z]{1,3}[+-]$", t):  # AA+, BBB-
                        return True
                    if re.match(r"^Prime-\d$", t):  # Prime-1
                        return True
                    if re.match(r"^[A-Z]\d$", t):  # F1
                        return True
                    # Common outlook/status values
                    if t.lower() in (
                        "stable",
                        "positive",
                        "negative",
                        "watch",
                        "developing",
                    ):
                        return True
                col_pos += cs
            return False

        # Helper to check if row is a title row (single cell spanning most of table)
        def is_title_row(row, total_cols):
            """Check if this row is a title/description spanning most of the table."""
            non_empty_cells = []
            total_span = 0
            for text, colspan in row:
                t = (
                    text.replace("\u200b", "")
                    .replace("\u200c", "")
                    .replace("\u200d", "")
                    .replace("\ufeff", "")
                    .strip()
                )
                total_span += colspan
                if t:
                    non_empty_cells.append((t, colspan))

            # If single text cell spans majority of the table width, it's a title row
            # This catches company names, statement titles, period descriptions, etc.
            if len(non_empty_cells) == 1:
                text, colspan = non_empty_cells[0]
                # Single cell spanning >= 40% of columns is a title/category row
                # Lower threshold to catch super-headers like "Total Stockholders' Equity"
                if colspan >= total_cols * 0.4:
                    return True
            return False

        # Find consecutive header rows (non-empty, non-data rows)
        header_rows: list = []

        # Only use <th>/<td> as a hard "data row" signal when the table mixes
        # them.  Old SEC HTML often uses <td> for every cell — including headers
        # — so when every row is all-<td> we must rely on is_data_row() alone.
        _some_th_rows = bool(row_has_th_flags and any(row_has_th_flags))

        for row_idx, row in enumerate(rows_with_cs):
            # In tables that mix <th> and <td>, a row with only <td> cells is
            # definitely a data row — stop collecting headers here.
            if (
                _some_th_rows
                and row_idx < len(row_has_th_flags)  # type: ignore
                and not row_has_th_flags[row_idx]  # type: ignore
            ):
                # Row has only <td> elements in a table that mixes th/td - data row
                break

            # Check for empty row
            has_content = any(is_header_text(text) for text, _ in row)
            if not has_content:
                if header_rows:
                    continue  # Skip empty rows between header rows
                continue

            # Check if this is a data row
            if is_data_row(row):
                break

            # Skip title/description rows that span most of the table
            if is_title_row(row, total_cols):
                continue

            # Check if this is a section label in column 0 (like "Assets:" or "Liabilities:")
            # Section labels can have colspan > 1 for formatting but are still a single label
            non_empty_cells = [
                (text.replace("\u200b", "").strip(), cs, idx)
                for idx, (text, cs) in enumerate(row)
                if text.replace("\u200b", "").strip()
            ]
            if len(non_empty_cells) == 1:
                text, cs, cell_idx = non_empty_cells[0]
                # Section label detection:
                # 1. Single non-empty cell at the start of the row (first few positions)
                # 2. Text ends with ":" (like "Assets:", "Liabilities and Equity:")
                # 3. OR small colspan (1-3) in first position - generic label
                # BUT: Don't treat years as section labels - they're data markers
                is_year_label = bool(re.match(r"^(19|20)\d{2}$", text.strip()))
                is_section_label = False
                if not is_year_label and (
                    cell_idx == 0 or cs >= 2
                ):  # First cell or spanning cell
                    if text.endswith(":"):
                        # Explicit section label like "Assets:" or "Liabilities:"
                        is_section_label = True
                    elif cs <= 3 and cell_idx == 0:
                        # Small colspan single text at start - likely a label
                        is_section_label = True

                if is_section_label:
                    if header_rows:
                        break
                    continue

            header_rows.append((row_idx, row))

        # Need at least 2 header rows for vertical merging to be useful
        if len(header_rows) < 2:
            return None, 0

        # Build per-row cell maps: start_pos -> (text, end_pos_inclusive)
        #
        # We intentionally store only the START position of each cell (not all
        # positions within its span).  Parent cells like "2007" (colspan=6) and
        # child cells like "Instruments" (colspan=2) therefore get distinct
        # entries at their respective starting positions.  The "covers" check
        # below (start <= leaf_pos <= end) is then used to find the cell that
        # covers any given leaf column position.
        row_cell_start_maps: list[dict] = []
        for _row_idx, row in header_rows:
            start_map: dict = {}
            col_pos = 0
            for text, colspan in row:
                t = (
                    text.replace("\u200b", "")
                    .replace("\u200c", "")
                    .replace("\u200d", "")
                    .replace("\ufeff", "")
                    .strip()
                )
                if t and is_header_text(t):
                    # (text, inclusive_end_position)
                    start_map[col_pos] = (t, col_pos + colspan - 1)
                col_pos += colspan
            if start_map:
                row_cell_start_maps.append(start_map)

        if not row_cell_start_maps:
            return None, 0

        # Leaf column positions = the UNION of all cell starting positions across
        # every header row.  Using the union (rather than just the row with the
        # most cells) ensures we capture columns that only appear in some rows.
        # Example – Commitments table:
        #   Row 0: "2008"(col2) "2009 -"(col4) "2011 -"(col6) "2013 -"(col8)   → 4 cells
        #   Row 1:              "2010"  (col4)  "2012"  (col6) "Thereafter"(col8) "Total"(col10) → 4 cells
        #   Union positions: [2, 4, 6, 8, 10]  → "Total" at col 10 is included.
        # Example – GS 2008 Financial Instruments staircase:
        #   Row 2: "Financial"(col6) "Financial"(col14)           → 2 cells
        #   Row 3: "Financial"(col2) "Instruments"(col6) ...      → 4 cells
        #   Union positions: [2, 6, 10, 14]  → same as max-cells approach.
        leaf_positions: list = sorted(set().union(*row_cell_start_maps))

        if not leaf_positions or len(leaf_positions) < 2:
            return None, 0

        # For each leaf position, walk all header rows top-to-bottom and collect
        # the text of the cell that COVERS that position
        # (i.e. cell_start <= leaf_pos <= cell_end).  Consecutive identical
        # texts are deduplicated so a parent "2007" that covers multiple leaf
        # columns doesn't repeat within the merged string for a single column.
        merged_headers: list = []
        for leaf_pos in leaf_positions:
            parts: list = []
            last_text = None
            for sm in row_cell_start_maps:
                for start, (text, end) in sm.items():
                    if start <= leaf_pos <= end:
                        if text != last_text:
                            parts.append(text)
                            last_text = text
                        break  # only one cell can cover a position per row
            if parts:
                merged_headers.append(" ".join(parts))

        if not merged_headers:
            return None, 0

        # If position 0 is not a leaf column it is the empty label column.
        is_label_col = 0 not in leaf_positions

        # Return as a single merged header layer.
        header_row_count = max(row_idx for row_idx, _ in header_rows) + 1
        prefix: list = [""] if is_label_col else []
        return [prefix + merged_headers], header_row_count