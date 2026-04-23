def render(self) -> str:
        string_rows = [[""] + self.column_keys]
        string_rows.extend(r.as_column_strings() for r in self.rows)
        num_cols = max(len(i) for i in string_rows)
        for sr in string_rows:
            sr.extend(["" for _ in range(num_cols - len(sr))])

        col_widths = [max(len(j) for j in i) for i in zip(*string_rows, strict=True)]
        finalized_columns = ["  |  ".join(i.center(w) for i, w in zip(string_rows[0], col_widths, strict=True))]
        overall_width = len(finalized_columns[0])
        for string_row, row in zip(string_rows[1:], self.rows, strict=True):
            finalized_columns.extend(row.row_separator(overall_width))
            finalized_columns.append("  |  ".join(row.finalize_column_strings(string_row, col_widths)))

        newline = "\n"
        has_warnings = self._highlight_warnings and any(ri.has_warnings for ri in self.results)
        return f"""
[{(' ' + (self.label or '') + ' ').center(overall_width - 2, '-')}]
{newline.join(finalized_columns)}

Times are in {common.unit_to_english(self.time_unit)}s ({self.time_unit}).
{'(! XX%) Measurement has high variance, where XX is the IQR / median * 100.' + newline if has_warnings else ""}"""[1:]