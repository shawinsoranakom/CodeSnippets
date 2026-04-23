def _summarize_candidate_tables(
        self, tables: list[ExcelTable]
    ) -> dict[str, float | int]:
        table_count = len(tables)
        real_singleton_count = 0
        severe_separator_count = 0
        sparse_large_table_count = 0
        total_area = 0
        weighted_blank_numerator = 0.0
        total_interior_blank_lines = 0
        total_possible_interior_lines = 0
        row_cover_count = collections.Counter()

        for table in tables:
            table_summary = self._summarize_table_for_gap_selection(table)
            table_area = int(table_summary["table_area"])
            blank_ratio = float(table_summary["blank_ratio"])
            interior_blank_row_count = int(table_summary["interior_blank_row_count"])
            interior_blank_col_count = int(table_summary["interior_blank_col_count"])
            max_consecutive_interior_blank_lines = int(
                table_summary["max_consecutive_interior_blank_lines"]
            )

            total_area += table_area
            weighted_blank_numerator += table_area * blank_ratio
            total_interior_blank_lines += (
                interior_blank_row_count + interior_blank_col_count
            )
            total_possible_interior_lines += max(table.num_rows - 2, 0) + max(
                table.num_cols - 2, 0
            )
            for row_idx in range(table.anchor[1], table.anchor[1] + table.num_rows):
                row_cover_count[row_idx] += 1

            if bool(table_summary["real_singleton"]):
                real_singleton_count += 1
            if table_area >= 6 and blank_ratio > 0.35:
                sparse_large_table_count += 1
            if max_consecutive_interior_blank_lines >= 2:
                severe_separator_count += 1

        occupied_row_count = max(len(row_cover_count), 1)
        row_overlap_excess_ratio = sum(
            max(0, count - 1) for count in row_cover_count.values()
        ) / occupied_row_count

        return {
            "real_singleton_ratio": real_singleton_count / max(table_count, 1),
            "weighted_blank_ratio": weighted_blank_numerator / max(total_area, 1),
            "interior_blank_line_ratio": total_interior_blank_lines
            / max(total_possible_interior_lines, 1),
            "sparse_large_table_ratio": sparse_large_table_count / max(table_count, 1),
            "severe_separator_count": severe_separator_count,
            "row_overlap_excess_ratio": row_overlap_excess_ratio,
        }