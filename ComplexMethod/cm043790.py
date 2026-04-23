def process_equity_statement_table(rows, rows_with_colspan):
    """Process equity statement table with stacked vertical headers.

    Returns (processed_rows, header_count) or (None, 0) if not applicable.
    """
    # Step 1: Find first data row (row with actual numeric values)
    data_start_idx = 0

    for i, row in enumerate(rows):
        non_empty = [c.strip() for c in row if c.strip()]
        if not non_empty:
            continue

        row_text_lower = " ".join(c.lower() for c in non_empty)

        # Check for $ followed by number pattern (indicates data row)
        # Look for actual balance/value data with $ prefix
        has_balance_data = False
        for j, cell in enumerate(row):
            c = cell.strip()
            next_c = row[j + 1].strip() if j + 1 < len(row) else ""

            # Pattern 1: Combined dollar amounts like "$21,789" or "$5,303"
            if (
                (c.startswith("$") and len(c) > 1 and any(ch.isdigit() for ch in c))
                or c == "$"
                and next_c
                and any(ch.isdigit() for ch in next_c)
            ) and "balance" in row_text_lower:
                has_balance_data = True
                break

        if has_balance_data:
            data_start_idx = i
            break

    if data_start_idx == 0 or data_start_idx >= len(rows):
        return None, 0

    # Step 2: Analyze a data row to find the column structure
    # Each logical value column has: possibly spacer + $ cell + number cell
    # Find all columns that directly contain $ + number format
    sample_row = rows[data_start_idx]
    value_positions = []  # (col_index, value_with_$)

    for j, cell in enumerate(sample_row):
        c = cell.strip()
        # Match "$21,789" or "$(24,094)" or "$5,165" patterns
        if c and re.match(r"^[\$][\(\)]?[\d,]+[\)]?$", c):
            value_positions.append(j)

    # If $ and value are in separate cells, find pairs
    if not value_positions:
        for j, cell in enumerate(sample_row[:-1]):
            c = cell.strip()
            next_c = sample_row[j + 1].strip() if j + 1 < len(sample_row) else ""
            # $ in current cell, number in next
            if c == "$" and next_c and re.match(r"^[\(\)]?[\d,]+[\)]?$", next_c):
                value_positions.append(j)  # Use the $ cell position as anchor
            elif c in ["$(", "($"] and next_c and re.match(r"^[\d,]+\)?$", next_c):
                value_positions.append(j)

    num_value_cols = len(value_positions)
    if num_value_cols < 2:
        return None, 0

    # Step 3: Build headers from header rows (rows before data_start_idx)
    # For each value position, find the corresponding header by looking at
    # which header text appears above or near that column

    def is_title_row(row_idx):
        """Identify if a row is a title/descriptor row that should be skipped from headers."""
        if row_idx >= len(rows):
            return False
        row = rows[row_idx]
        non_empty = [c.strip() for c in row if c.strip()]

        if not non_empty:
            return True  # Empty row - skip it

        if len(non_empty) == 1 and row_idx < len(rows_with_colspan):
            # Single non-empty cell - check if it spans most of the row
            # Also check rows_with_colspan for actual colspan info
            cs_row = rows_with_colspan[row_idx]
            cs_non_empty = [(t, cs) for t, cs in cs_row if t.strip()]

            if len(cs_non_empty) == 1:
                _, colspan = cs_non_empty[0]
                total_span = sum(cs for _, cs in cs_row)

                if colspan >= total_span * 0.4:  # Title spans 40%+ of table
                    return True

        return False

    # Filter header rows to exclude title rows
    header_rows = [i for i in range(data_start_idx) if not is_title_row(i)]
    # Build column boundaries: each value column "owns" cells from its position
    # back to the previous value's position (or start of row)
    col_boundaries = []

    for idx, v_pos in enumerate(value_positions):
        start = (
            0 if idx == 0 else value_positions[idx - 1] + 2
        )  # Skip to after previous value
        col_boundaries.append((start, v_pos + 1))  # inclusive range

    # First, find all unique header column positions from header rows
    header_positions: dict = {}  # col_idx -> [text1, text2, ...]

    for row_idx in header_rows:
        row = rows[row_idx]
        for col_idx, cell in enumerate(row):
            text = cell.strip()
            if text and not re.match(r"^[\$\d,\.\(\)]+$", text):
                if col_idx not in header_positions:
                    header_positions[col_idx] = []
                if text not in header_positions[col_idx]:
                    header_positions[col_idx].append(text)

    # Get unique header columns in sorted order (by position)
    sorted_header_cols = sorted(header_positions.keys())
    # Build headers from the stacked text at each position
    stacked_headers = []

    for h_pos in sorted_header_cols:
        parts = header_positions[h_pos]
        header_text = " ".join(parts)
        stacked_headers.append(header_text)

    # Match headers to values by sequence
    # If we have N values and M headers, match them by index
    final_headers = []

    for idx, v_pos in enumerate(value_positions):
        if idx < len(stacked_headers):
            final_headers.append(stacked_headers[idx])
        else:
            final_headers.append(f"Column {idx + 1}")

    # Step 4: Build output table
    result = []

    # Add header row (empty label + column headers)
    result.append([""] + final_headers)

    # Process each data row
    for row in rows[data_start_idx:]:
        # Extract label (first cell, or first non-$ non-empty cell)
        label = ""
        for cell in row[:3]:  # Label is usually in first few cells
            c = cell.strip()
            if (
                c
                and not c.startswith("$")
                and not re.match(r"^\s*[\(\)]?\s*[\d,]+\.?\d*\s*[\)\%]?$", c)
            ) and c not in [
                "$",
                "(",
                ")",
                "%",
                "—",
                "–",
                "-",
            ]:
                label = c
                break

        # Extract values from value positions
        values = []
        for v_pos in value_positions:
            val = ""
            if v_pos < len(row):
                c = row[v_pos].strip()
                # Check if this cell has the complete value ($ + number)
                if c and (c.startswith("$") or re.match(r"^[\(\)]?[\d,]+", c)):
                    val = c
                    # If it's just $, look at next cell
                    if c in ["$", "$(", "($"] and v_pos + 1 < len(row):
                        next_c = row[v_pos + 1].strip()
                        if next_c:
                            val = c + next_c
                elif v_pos + 1 < len(row):
                    # Value might be in next cell
                    next_c = row[v_pos + 1].strip()
                    if next_c and re.match(r"^[\(\)]?[\d,]+", next_c):
                        val = next_c
            values.append(val)

        # Skip rows with no label and no values
        if not label and not any(v.strip() for v in values):
            continue

        result.append([label] + values)

    return result, 1