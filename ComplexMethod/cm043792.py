def extract_periods_from_rows(
    rows_with_cs, row_has_th_flags=None, _year_pos_shift=None
):
    """Extract column headers from header rows.

    Args:
        rows_with_cs: List of rows, each row is list of (text, colspan) tuples
        row_has_th_flags: Optional list of booleans indicating if each row has <th> elements

    Returns (header_layers, header_row_count) where:
        header_layers: list of rows (each row is list of strings for each column)
        header_row_count: number of source rows consumed

    For multi-level headers (e.g., "Equipment Operations" spanning 2025/2024/2023),
    returns multiple header rows like:
        [["", "Equipment Operations", "Equipment Operations", ..., "Financial Services", ...],
         ["", "2025", "2024", "2023", "2025", ...]]
    """
    if not rows_with_cs:
        return [], 0

    # Calculate total columns from first row
    total_cols = sum(cs for _, cs in rows_with_cs[0]) if rows_with_cs else 0

    # Helper function to detect and merge vertical multi-row headers
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

    # Try multi-level header extraction first
    header_layers, header_row_count = build_column_headers_from_colspan(
        rows_with_cs, _year_pos_shift
    )
    # Only attempt vertical merging when build_column_headers_from_colspan found
    # nothing.  If it already returned a proper multi-layer result (e.g. 2007/2006
    # parent rows spanning child sub-headers) we must NOT flatten it into a single
    # merged row — that destroys the multi-index structure the caller depends on.
    vertical_headers, vertical_row_count = (None, 0)
    _colspan_has_year_range_fragments = (
        header_layers is not None
        and len(header_layers) == 1
        and any(
            # Match incomplete year-range fragments like "2009 -" that need
            # merging with a row below (e.g. "2010"), but NOT complete ranges
            # like "2027-2028" or "2029 - 2030" which are valid headers.
            re.match(r"^(19|20)\d{2}\s*[-\u2013\u2014]", h.strip())
            and not re.match(
                r"^(19|20)\d{2}\s*[-\u2013\u2014]\s*(19|20)\d{2}$", h.strip()
            )
            for h in header_layers[0]
            if h
        )
    )
    if header_row_count == 0 or _colspan_has_year_range_fragments:
        # Also try vertical header merging for two cases:
        #   1. Colspan extraction found nothing (header_row_count == 0).
        #      Example: "2009 -" / "2010" stacked → merged to "2009 - 2010"
        #   2. Colspan returned a flat single-layer with incomplete year-range fragments
        #      like "2009 -" (companion row wasn't merged by the month-year logic).
        #      Vertical merging will produce the correct e.g. "2009 - 2010" strings.
        if _colspan_has_year_range_fragments:
            # Discard the useless flat result so the vertical output wins below
            header_layers = None
            header_row_count = 0
        vertical_headers, vertical_row_count = merge_vertical_headers(
            rows_with_cs, total_cols, row_has_th_flags
        )
    # Decide which approach produced better headers
    # Prefer vertical merge if it created multi-word headers (indicating successful merge)
    use_vertical = False

    if vertical_headers and vertical_row_count > 0:
        # Check if vertical merge created multi-word headers
        vertical_multi_word = any(
            len(h.split()) >= 2
            for layer in vertical_headers
            for h in layer
            if h
            and not re.match(r"^[\(\)]*$", h)
            and not re.match(r"^(19|20)\d{2}$", h)
        )

        # Check if build_column_headers_from_colspan produced multi-word headers
        colspan_multi_word = False
        if header_layers:
            colspan_multi_word = any(
                len(h.split()) >= 2
                for layer in header_layers
                for h in layer
                if h
                and not re.match(r"^[\(\)]*$", h)
                and not re.match(r"^(19|20)\d{2}$", h)
            )

        # Prefer vertical if it merged headers but colspan approach didn't
        if vertical_multi_word and not colspan_multi_word:
            use_vertical = True
        # Also prefer vertical if it has more non-year headers (better merging)
        elif vertical_multi_word:
            vertical_non_year = sum(
                1
                for layer in vertical_headers
                for h in layer
                if h and not re.match(r"^(19|20)\d{2}$", h.strip())
            )
            colspan_non_year = (
                sum(
                    1
                    for layer in header_layers
                    for h in layer
                    if h and not re.match(r"^(19|20)\d{2}$", h.strip())
                )
                if header_layers
                else 0
            )
            if vertical_non_year >= colspan_non_year:
                use_vertical = True

    if use_vertical:
        # Validate: check for years/periods or financial terms
        all_header_text = " ".join(h for layer in vertical_headers for h in layer)  # type: ignore
        has_year_in_headers = bool(re.search(r"\b(19|20)\d{2}\b", all_header_text))
        has_period_in_headers = bool(
            re.search(
                r"(months?\s+ended|year\s+ended|weeks?\s+ended|quarter|period|fiscal)",
                all_header_text,
                re.I,
            )
        )
        has_year_in_rows = any(
            re.search(r"\b(19|20)\d{2}\b", text)
            for row in rows_with_cs[:vertical_row_count]
            for text, _ in row
        )
        has_year_after_headers = (
            any(
                re.search(r"\b(19|20)\d{2}\b", text)
                for row in rows_with_cs[vertical_row_count : vertical_row_count + 2]
                for text, _ in row
            )
            if vertical_row_count < len(rows_with_cs)
            else False
        )

        # Check for financial terms
        financial_terms = [
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
            r"\bweighted\b",
            r"\baverage\b",
            r"\baggregate\b",
            r"\bintrinsic\b",
            r"\bcontractual\b",
            r"\bremaining\b",
            r"\bexercisable\b",
            r"\bAmount\b",
            r"\bCredit\b",
            r"\bDebit\b",
            r"\bBalance\b",
            r"\bReceivables?\b",
            r"\bLeases?\b",
            r"\bNotes?\b",
            r"\bAccounts?\b",
            r"\bWholesale\b",
            r"\bRetail\b",
            r"\bFinancing\b",
            r"\bTotal\b",
            r"\bAllowance\b",
            r"\bProvision\b",
            r"\bRevolving\b",
            r"\bTax\b",
            r"\bExpense\b",
            r"\bIncome\b",
            r"\bLoss\b",
            r"\bGain\b",
        ]
        has_financial_terms = any(
            re.search(term, all_header_text, re.I) for term in financial_terms
        )

        merged_multi_word = any(
            len(h.split()) >= 2
            for layer in vertical_headers  # type: ignore
            for h in layer
            if h and not re.match(r"^[\(\)]*$", h)
        )

        if (
            has_year_in_headers
            or has_period_in_headers
            or has_year_in_rows
            or has_year_after_headers
        ):
            return vertical_headers, vertical_row_count

        if merged_multi_word and has_financial_terms:
            return vertical_headers, vertical_row_count

    # Fall back to colspan-based headers if available
    if header_layers and header_row_count > 0:
        # Check if we have meaningful multi-level headers
        # Look for years in any layer
        has_years = False

        for layer in header_layers:
            for h in layer:
                if re.search(r"\b(19|20)\d{2}\b", h):
                    has_years = True
                    break

            if has_years:
                break

        if has_years and len(header_layers) >= 1:
            return header_layers, header_row_count

    # Fall back to original single-row logic
    period_prefixes = []
    years: list = []
    generic_headers: list = []
    full_date_headers = []
    sub_headers = []
    period_parts = []
    ended_parts = []
    as_of_prefix = ""

    # Only look at first 10 rows for headers (not data rows at the bottom)
    for row_idx, row in enumerate(rows_with_cs[:10]):
        texts = [t.strip() for t, cs in row if t.strip()]
        if not texts:
            continue

        row_text = " ".join(texts)

        # Look for period descriptions (e.g., "Three Months Ended May")
        if re.search(
            r"(months?\s+ended|year\s+ended|quarter\s+ended|weeks?\s+ended)",
            row_text,
            re.I,
        ):
            prefixes = [
                t
                for t in texts
                if re.search(r"(months?|year|quarter|weeks?)\s+ended", t, re.I)
            ]
            if prefixes:
                period_prefixes = prefixes

        # Check individual cells, not the joined row_text
        period_cell_matches = [
            t
            for t in texts
            if re.match(
                r"^(Three|Six|Nine|Twelve|[1-9]|[1-4]\d|5[0-3])\s+(Months?|Weeks?|Week Ended)$",
                t,
                re.I,
            )
            or re.match(r"^(Fiscal\s+)?(Year|Quarter)$", t, re.I)
        ]

        if period_cell_matches:
            period_parts = period_cell_matches

        # Look for "Ended May" or "Ended" continuation row
        ended_cell_matches = [t for t in texts if re.match(r"^Ended\b", t, re.I)]

        if ended_cell_matches and period_parts:
            ended_parts = ended_cell_matches
            # Combine with period_parts to make full prefixes
            if len(ended_parts) == len(period_parts):
                period_prefixes = [
                    f"{p} {e}" for p, e in zip(period_parts, ended_parts)
                ]
            elif len(ended_parts) == 1:
                # Same "Ended X" for all periods
                period_prefixes = [f"{p} {ended_parts[0]}" for p in period_parts]

        # Look for "As of" prefix row (for balance sheets)
        if re.match(r"^As\s+of$", row_text, re.I):
            as_of_prefix = "As of"

        # These are Month + Year in a single cell (possibly with "As of" prefix)
        date_pattern = rf"^(As\s+of\s+)?({MONTHS_PATTERN})\s+((?:19|20)\d{{2}})$"
        date_matches = [t for t in texts if re.match(date_pattern, t, re.I)]
        if len(date_matches) >= 2:
            full_date_headers = date_matches

        # Look for sub-headers like "Assets | Liabilities" that should combine with parent headers
        # These typically appear in rows with repeating short column labels
        sub_header_pattern = r"^(Assets|Liabilities|Actual|Pro\s*Forma|Adjustments)$"
        sub_matches = [t for t in texts if re.match(sub_header_pattern, t, re.I)]
        if len(sub_matches) >= 2:
            sub_headers = sub_matches

        # Look for years - but only standalone years, not years in parentheses (effective dates)
        # or years embedded in long descriptive text
        year_cells = []
        for t in texts:
            # Skip cells that are too long to be column headers
            if len(t) > 50:
                continue
            # Skip cells with years in parentheses like "(2020)" - these are effective dates
            if re.search(r"\(\d{4}\)", t):
                continue
            # Skip cells where year is part of a longer descriptive header
            # like "Executive Contributions in FY 2025 ($)" or "Aggregate Balance at FY 2025-end"
            # These are descriptive column headers, not year column headers
            if len(t) > 20 and re.search(
                r"(contributions?|balance|earnings|aggregate|withdrawals?|distributions?)",
                t,
                re.I,
            ):
                continue
            # Skip cells that are full dates (e.g., "April 7, 2025")
            # These are data values, not year column headers
            if re.match(
                rf"({MONTHS_PATTERN})\s+\d{{1,2}},?\s*(19|20)\d{{2}}",
                t,
                re.I,
            ):
                continue
            # Look for standalone years or years in simple header formats
            match = re.search(r"\b((?:19|20)\d{2})\b", t)
            if match:
                year_cells.append(match.group(1))
        if len(year_cells) >= 2 and not years:
            years = year_cells

        # Look for generic column headers ONLY in first few rows
        # Must be: non-numeric text, multiple items, short length, row has no data
        if row_idx < 5 and not generic_headers:
            # Skip descriptor rows like "(in millions...)"
            if row_text.startswith("("):
                continue
            # Skip rows with numbers that look like data (commas in numbers or decimals)
            if re.search(r"\d{1,3}(,\d{3})+|\d+\.\d{2}", row_text):
                continue
            # Candidates: short text items that are not numbers
            candidates = [
                t
                for t in texts
                if 2 <= len(t) <= 30
                and not re.match(r"^[\d\.,x\-]+$", t)
                and not t.startswith("(")
            ]
            if len(candidates) >= 2:
                # Check if these look like headers (mostly alphabetic)
                alpha_count = sum(1 for c in candidates if re.match(r"^[A-Za-z]", c))
                if alpha_count >= 2:
                    generic_headers = candidates

    # Priority 1: Full date headers with sub-headers (e.g., "As of May 1999" + "Assets/Liabilities")
    if full_date_headers and sub_headers:
        # Combine parent headers with sub-headers
        combined = []
        subs_per_parent = len(sub_headers) // len(full_date_headers)

        if subs_per_parent > 0:
            for i, parent in enumerate(full_date_headers):
                for j in range(subs_per_parent):
                    sub_idx = i * subs_per_parent + j

                    if sub_idx < len(sub_headers):
                        combined.append(f"{parent} {sub_headers[sub_idx]}")

            if combined:
                # Return as two rows: parent row and sub row
                parent_row = [""]
                sub_row = [""]

                for i, parent in enumerate(full_date_headers):
                    for j in range(subs_per_parent):
                        parent_row.append(parent)
                        sub_idx = i * subs_per_parent + j

                        if sub_idx < len(sub_headers):
                            sub_row.append(sub_headers[sub_idx])

                return [parent_row, sub_row], 2

    # Priority 2: Full date headers without sub-headers
    if full_date_headers:
        headers = (
            [f"{as_of_prefix} {d}" for d in full_date_headers]
            if as_of_prefix
            else full_date_headers
        )
        return [[""] + headers], 1

    # Priority 3: Combine prefixes with years
    if period_prefixes and years:
        # Check if prefixes already contain years (e.g., "For the Three Months Ended January 26, 2025")
        # Count how many years are mentioned in the prefixes
        prefix_year_counts = []

        for p in period_prefixes:
            year_matches = re.findall(r"\b(19|20)\d{2}\b", p)
            prefix_year_counts.append(len(year_matches))

        # If any prefix contains multiple years (describes multiple periods),
        # skip using prefixes and just use the years
        if any(count > 1 for count in prefix_year_counts):
            return [[""] + years], 1

        # If each prefix has exactly one year and matches the number of years,
        # use prefixes directly (they're full period descriptions)
        if all(count == 1 for count in prefix_year_counts) and len(
            period_prefixes
        ) == len(years):
            return [[""] + period_prefixes], 1

        periods = []
        prefix_idx = 0

        for i, year in enumerate(years):
            if prefix_idx < len(period_prefixes):
                prefix = period_prefixes[prefix_idx]
                # Only append year if prefix doesn't already have it
                if not re.search(r"\b" + year + r"\b", prefix):
                    periods.append(f"{prefix} {year}")
                else:
                    periods.append(prefix)
                # Advance prefix index every N years based on ratio
                years_per_prefix = len(years) // len(period_prefixes)
                if years_per_prefix > 0 and (i + 1) % years_per_prefix == 0:
                    prefix_idx += 1
            else:
                periods.append(year)
        return [[""] + periods], 1

    if years:
        return [[""] + years], 1

    if generic_headers:
        # No financial periods, use generic headers
        return [[""] + generic_headers], 1

    return [], 0