def collapse_repeated_headers(rows):
    """Collapse adjacent duplicate header cells from colspan expansion.

    When header cells have colspan>1, they get expanded to multiple cells
    with the same text. Data cells in those spans typically only fill one
    position. After remove_empty_columns, we may have:
      Header: ["Name", "Fiscal Year", "", "Salary", "", "Bonus", ...]
      Data:   ["Ellison", "", "2025", "", "950,000", "", ...]

    This function collapses repeated adjacent headers and shifts data to align:
      Header: ["Name", "Fiscal Year", "Salary", "Bonus", ...]
      Data:   ["Ellison", "2025", "950,000", ...]
    """
    if not rows or len(rows) < 2:
        return rows

    header = rows[0]
    if len(header) < 2:
        return rows

    # Identify positions to collapse: where header[i] == header[i-1] and both non-empty
    # OR where header[i] is empty but header[i-1] is not (empty trailing from colspan)
    cols_to_remove = set()
    for i in range(1, len(header)):
        prev = header[i - 1].strip() if header[i - 1] else ""
        curr = header[i].strip() if header[i] else ""

        # If current is duplicate of previous OR empty with non-empty prev
        # AND the data rows mostly have content in current (not prev)
        if prev and (curr == prev or not curr):
            # Check if data rows have content in THIS column vs PREV column
            # If data is in current column, keep current and remove previous
            # If data is in previous column, remove current
            prev_has_data = any(
                i - 1 < len(row) and row[i - 1].strip() for row in rows[1:]
            )
            curr_has_data = any(i < len(row) and row[i].strip() for row in rows[1:])

            if curr_has_data and not prev_has_data:
                # Data is in current column, remove the previous header duplicate
                # and copy header text to current
                header[i] = prev  # Copy header to data position
                cols_to_remove.add(i - 1)
            elif not curr_has_data and prev_has_data:
                # Data is in previous column, just remove current empty
                cols_to_remove.add(i)
            elif not curr_has_data and not prev_has_data:
                # Neither has data, remove the empty trailing
                if not curr:
                    cols_to_remove.add(i)
            elif curr_has_data and prev_has_data and not curr:
                # Both have data, but header is only in prev (curr is empty).
                # Check if data is complementary: no row has data in BOTH columns.
                # This happens with $ prefix columns in SEC tables where dollar rows
                # put merged $+value at a different position than non-dollar rows.
                is_complementary = True
                for row in rows[1:]:
                    p = row[i - 1].strip() if i - 1 < len(row) else ""
                    c = row[i].strip() if i < len(row) else ""
                    if p and c:
                        is_complementary = False
                        break
                if is_complementary:
                    # Merge: move curr's data into prev's empty slots, remove curr
                    for row in rows[1:]:
                        c = row[i].strip() if i < len(row) else ""
                        p = row[i - 1].strip() if i - 1 < len(row) else ""
                        if c and not p:
                            row[i - 1] = row[i]
                    cols_to_remove.add(i)

    if not cols_to_remove:
        # Still check for trailing empty columns
        pass

    # Second pass: detect complementary adjacent columns caused by
    # $ prefix merging offset. When $ is in a separate cell, the merged
    # $+value lands at a different expanded position than non-dollar values.
    # Result: adjacent columns with complementary data (never both non-empty
    # in the same row). Merge the smaller into the larger regardless of
    # whether rows[0] has header text.
    for i in range(1, len(header)):
        if i in cols_to_remove or (i - 1) in cols_to_remove:
            continue  # Already handled

        # Check if columns i-1 and i are strictly complementary across ALL rows
        is_complementary = True
        col_prev_count = 0
        col_curr_count = 0
        for row in rows:
            p = row[i - 1].strip() if i - 1 < len(row) else ""
            c = row[i].strip() if i < len(row) else ""
            if p and c:
                is_complementary = False
                break
            if p:
                col_prev_count += 1
            if c:
                col_curr_count += 1

        if not is_complementary:
            continue
        if col_curr_count == 0:
            continue  # col i is fully empty, remove_empty_columns handles it

        # Merge smaller into larger (by count of non-empty rows)
        if col_prev_count >= col_curr_count:
            # Merge col i data into col i-1
            for row in rows:
                c = row[i].strip() if i < len(row) else ""
                p = row[i - 1].strip() if i - 1 < len(row) else ""
                if c and not p:
                    row[i - 1] = row[i]
            cols_to_remove.add(i)
        else:
            # Merge col i-1 data into col i
            for row in rows:
                p = row[i - 1].strip() if i - 1 < len(row) else ""
                c = row[i].strip() if i < len(row) else ""
                if p and not c:
                    row[i] = row[i - 1]
            cols_to_remove.add(i - 1)

    # Also remove trailing empty columns (both header and all data empty)
    num_cols = len(header)
    for col_idx in range(num_cols - 1, -1, -1):
        header_empty = not (header[col_idx].strip() if col_idx < len(header) else "")
        data_empty = all(
            not (row[col_idx].strip() if col_idx < len(row) else "") for row in rows[1:]
        )
        if header_empty and data_empty:
            cols_to_remove.add(col_idx)
        else:
            break  # Stop at first non-empty column from the right

    if not cols_to_remove:
        return rows

    # Rebuild all rows without the collapsed columns
    cols_to_keep = [i for i in range(len(header)) if i not in cols_to_remove]
    result = []
    for row in rows:
        new_row = [row[i] if i < len(row) else "" for i in cols_to_keep]
        result.append(new_row)

    return result