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