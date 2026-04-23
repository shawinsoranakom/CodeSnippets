def merge_split_rows(rows, rows_with_colspan):
    """Merge consecutive rows that are continuations of split text."""
    merged_data = []
    merged_colspan = []
    i = 0
    while i < len(rows):
        row = rows[i]
        row_cs = rows_with_colspan[i] if i < len(rows_with_colspan) else []
        row_text = " ".join(c.strip() for c in row if c.strip())

        # ── New: label-continuation merge ──────────────────────────────────
        # Detect rows whose label cell (col 0) has text but all other cells
        # are empty, AND the next row's label starts with a lowercase word
        # (i.e. it is a sentence continuation, e.g.
        #   Row A: "Level 3 assets for which we do not"
        #   Row B: "bear economic exposure (7)" | (14,437) | …
        # → Merge to: "Level 3 assets for which we do not bear economic exposure (7)"
        # and take the data values from Row B.
        non_empty_cols = [j for j, c in enumerate(row) if c.strip()]
        if len(non_empty_cols) == 1 and non_empty_cols[0] == 0 and i + 1 < len(rows):
            next_row = rows[i + 1]
            next_label = next_row[0].strip() if next_row else ""
            # Continuation: next label starts with a lowercase letter
            if next_label and next_label[0].islower():
                label_a = row[0].strip()
                merged_label = label_a + " " + next_label
                # Build merged row: combined label, then data columns from next row
                new_row = [merged_label] + list(next_row[1:])
                next_cs = (
                    rows_with_colspan[i + 1] if i + 1 < len(rows_with_colspan) else []
                )
                merged_data.append(new_row)
                merged_colspan.append(next_cs)
                i += 2
                continue
        # ───────────────────────────────────────────────────────────────────

        # Check if this row starts an incomplete parenthetical
        # Pattern: starts with ( but doesn't end with )
        # BUT only if the first non-empty cell itself has an unbalanced paren.
        # e.g., "(in millions, except per" is incomplete → merge with "share amounts)"
        # but "(in millions)" is complete → do NOT merge even if other cells follow.
        # Also "(Benefit from) provision for taxes" has balanced parens even
        # though it doesn't end with ")" — still complete, don't merge.
        if row_text.startswith("(") and not row_text.endswith(")"):
            # Check if the first non-empty cell has balanced parentheses
            first_cell = ""
            for c in row:
                if c.strip():
                    first_cell = c.strip()
                    break
            first_cell_balanced = first_cell.count("(") == first_cell.count(")")
            if first_cell_balanced:
                # First cell has balanced parens like "(in millions)" or
                # "(Benefit from) provision for income taxes" —
                # don't try to merge with subsequent rows
                merged_data.append(row)
                merged_colspan.append(row_cs)
                i += 1
                continue

            # If non-label columns have content, this is a header row
            # where the descriptor sits at col 0 alongside date/year
            # columns.  Don't merge — the unbalanced paren is just the
            # descriptor wrapping across the HTML row, and the data in
            # other columns must be preserved.
            non_label_content = any(c.strip() for c in row[1:])
            if non_label_content:
                merged_data.append(row)
                merged_colspan.append(row_cs)
                i += 1
                continue

            # Look ahead for continuation
            merged_text = row_text
            j = i + 1
            while j < len(rows):
                next_row = rows[j]
                next_text = " ".join(c.strip() for c in next_row if c.strip())
                # Check if next row is continuation (ends with ) or has amounts/share text)
                if next_text and (
                    next_text.endswith(")")
                    or "amount" in next_text.lower()
                    or "share" in next_text.lower()
                    or next_text.startswith("and ")
                ):
                    merged_text += " " + next_text
                    j += 1
                    if next_text.endswith(")"):
                        break
                else:
                    break

            if j > i + 1:
                # We merged rows - create single row with combined text
                new_row = [merged_text] + [""] * (len(row) - 1)
                merged_data.append(new_row)
                # For colspan, just use first row's structure
                merged_colspan.append(row_cs)
                i = j
                continue

        merged_data.append(row)
        merged_colspan.append(row_cs)
        i += 1

    return merged_data, merged_colspan