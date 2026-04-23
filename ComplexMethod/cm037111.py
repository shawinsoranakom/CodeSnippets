def generate_metric_table(self) -> str:
        stats_counts = Counter(self.stats)

        # Convert stats to rows of strings, in descending order of observed frequencies
        rows = []
        for stat, count in sorted(
            stats_counts.items(), key=lambda item: item[1], reverse=True
        ):
            rows.append(
                [
                    str(stat.num_unpadded_tokens),
                    str(stat.num_padded_tokens),
                    str(stat.num_paddings),
                    stat.runtime_mode,
                    str(count),
                ]
            )

        # Calculate column widths (max of header and data)
        col_widths = []
        for i, header_text in enumerate(self.COLUMN_HEADERS):
            max_width = len(header_text)
            for row in rows:
                max_width = max(max_width, len(row[i]))
            col_widths.append(max_width)

        table_header_list = [
            h.ljust(w) for h, w in zip(self.COLUMN_HEADERS, col_widths)
        ]
        table_header = "| " + " | ".join(table_header_list) + " |\n"

        table_separator = "|" + "|".join("-" * (w + 2) for w in col_widths) + "|\n"

        # Create data rows with proper alignment
        data_rows = []
        for row in rows:
            formatted_row = [
                str(val).ljust(width) for val, width in zip(row, col_widths)
            ]
            data_rows.append("| " + " | ".join(formatted_row) + " |")

        return (
            self.settings_header
            + table_header
            + table_separator
            + "\n".join(data_rows)
            + "\n"
        )