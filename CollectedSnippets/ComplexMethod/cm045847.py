def _summarize_table_for_gap_selection(
        self, excel_table: ExcelTable
    ) -> dict[str, float | int | bool]:
        table_area = excel_table.num_rows * excel_table.num_cols
        content_mask = self._build_table_content_mask(excel_table)
        content_area = sum(sum(1 for flag in row if flag) for row in content_mask)
        blank_ratio = 1.0 - (content_area / max(table_area, 1))

        interior_blank_rows = [
            not any(content_mask[row_idx])
            for row_idx in range(1, max(excel_table.num_rows - 1, 1))
        ]
        interior_blank_cols = [
            not any(content_mask[row_idx][col_idx] for row_idx in range(excel_table.num_rows))
            for col_idx in range(1, max(excel_table.num_cols - 1, 1))
        ]
        if excel_table.num_rows <= 2:
            interior_blank_rows = []
        if excel_table.num_cols <= 2:
            interior_blank_cols = []

        interior_blank_row_count = sum(interior_blank_rows)
        interior_blank_col_count = sum(interior_blank_cols)
        max_consecutive_interior_blank_lines = max(
            self._count_max_consecutive_true(interior_blank_rows),
            self._count_max_consecutive_true(interior_blank_cols),
        )

        return {
            "table_area": table_area,
            "content_area": content_area,
            "blank_ratio": blank_ratio,
            "interior_blank_row_count": interior_blank_row_count,
            "interior_blank_col_count": interior_blank_col_count,
            "max_consecutive_interior_blank_lines": max_consecutive_interior_blank_lines,
            "real_singleton": self._is_real_singleton_table(excel_table),
        }