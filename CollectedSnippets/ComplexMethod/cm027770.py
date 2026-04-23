def swap_entries_for_ellipses(
        self,
        row_index: Optional[int] = None,
        col_index: Optional[int] = None,
        height_ratio: float = 0.65,
        width_ratio: float = 0.4
    ):
        rows = self.get_rows()
        cols = self.get_columns()

        avg_row_height = rows.get_height() / len(rows)
        vdots_height = height_ratio * avg_row_height

        avg_col_width = cols.get_width() / len(cols)
        hdots_width = width_ratio * avg_col_width

        use_vdots = row_index is not None and -len(rows) <= row_index < len(rows)
        use_hdots = col_index is not None and -len(cols) <= col_index < len(cols)

        if use_vdots:
            for column in cols:
                # Add vdots
                dots = Tex(R"\vdots")
                dots.set_height(vdots_height)
                self.swap_entry_for_dots(column[row_index], dots)
        if use_hdots:
            for row in rows:
                # Add hdots
                dots = Tex(R"\hdots")
                dots.set_width(hdots_width)
                self.swap_entry_for_dots(row[col_index], dots)
        if use_vdots and use_hdots:
            rows[row_index][col_index].rotate(-45 * DEG)
        return self