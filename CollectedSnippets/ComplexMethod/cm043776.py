def remove_empty_columns(rows):
    """Remove columns that are empty across all rows."""
    if not rows:
        return rows
    num_cols = max(len(row) for row in rows)
    cols_to_keep = []
    for col_idx in range(num_cols):
        has_any_content = any(
            col_idx < len(row) and row[col_idx].strip().strip(INVISIBLE_CHARS)
            for row in rows
        )
        if has_any_content:
            cols_to_keep.append(col_idx)
    result = [[row[i] if i < len(row) else "" for i in cols_to_keep] for row in rows]
    return result