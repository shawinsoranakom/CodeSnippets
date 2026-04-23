def merge_split_cells(rows):
    """Merge cells that contain parts of the same value.

    IMPORTANT: When merging, we add an empty placeholder to maintain column
    alignment across all rows. Otherwise, rows with merged cells would have
    fewer columns than rows without merges, causing misalignment.
    """
    result = []
    for row in rows:
        merged_row = []
        i = 0
        while i < len(row):
            cell = row[i]
            cell_stripped = cell.strip()

            # Look ahead to see if next cell should be merged
            if i + 1 < len(row):
                next_cell = row[i + 1].strip()

                # Case 1: Cell ends with "(" and next cell is just ")"
                # e.g., "(306" + ")" → "(306)"
                if cell_stripped.endswith("(") and next_cell == ")":
                    merged_row.append(cell_stripped + ")")
                    merged_row.append("")  # Placeholder to maintain column count
                    i += 2
                    continue

                # Case 2: Cell is a number and next cell is just a closing paren
                # e.g., "(306" in cell, ")" in next cell for alignment
                # This handles negative numbers where open paren is with number
                if re.match(r"^\([\d,\.]+$", cell_stripped) and next_cell == ")":
                    merged_row.append(cell_stripped + ")")
                    merged_row.append("")  # Placeholder to maintain column count
                    i += 2
                    continue

                # Case 3: Cell is a number and next cell is a footnote marker
                # e.g., "2,264" + "(1)" → "2,264 (1)"
                # Only merge footnotes with 1-2 digits; 3+ digits like
                # "(193)" are negative financial values, not footnotes.
                if re.match(r"^[\$]?[\d,\.]+$", cell_stripped) and re.match(
                    r"^\(\d{1,2}\)$", next_cell
                ):
                    merged_row.append(cell_stripped + " " + next_cell)
                    merged_row.append("")  # Placeholder to maintain column count
                    i += 2
                    continue

                # Case 4: Cell is a number and a nearby cell is "%" or "pts"
                # SEC tables split "22%" across cells: "22"[cs=2] + "%"[cs=1]
                # After colspan expansion this becomes: "22", "", "%"
                # Also handles: "(1.2)" + "" + "pts" → "(1.2)pts"
                if re.match(r"^[\(\)]?[\d,\.]+[\)]?$", cell_stripped):
                    # Look for "%" or "pts" up to 2 cells ahead (skipping empties)
                    suffix_offset = None
                    for look in range(1, min(3, len(row) - i)):
                        look_cell = row[i + look].strip()
                        if look_cell in ("%", "pts"):
                            suffix_offset = look
                            break
                        if look_cell != "":
                            break  # Non-empty, non-suffix cell - stop

                    if suffix_offset is not None:
                        suffix = row[i + suffix_offset].strip()
                        merged_row.append(cell_stripped + suffix)
                        # Add empty placeholders for all consumed cells
                        for _ in range(suffix_offset):
                            merged_row.append("")
                        i += suffix_offset + 1
                        continue

            merged_row.append(cell)
            i += 1

        result.append(merged_row)
    return result