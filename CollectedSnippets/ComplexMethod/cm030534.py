def draw_column_headers(self, line, width):
        """Draw column headers with sort indicators."""
        # Determine which columns to show based on width
        show_sample_pct = width >= WIDTH_THRESHOLD_SAMPLE_PCT
        show_tottime = width >= WIDTH_THRESHOLD_TOTTIME
        show_cumul_pct = width >= WIDTH_THRESHOLD_CUMUL_PCT
        show_cumtime = width >= WIDTH_THRESHOLD_CUMTIME

        sorted_header = self.colors["sorted_header"]
        normal_header = self.colors["normal_header"]

        # Determine which column is sorted
        sort_col = {
            "nsamples": 0,
            "sample_pct": 1,
            "tottime": 2,
            "cumul_pct": 3,
            "cumtime": 4,
        }.get(self.collector.sort_by, -1)

        # Build the full header line first, then draw it
        # This avoids gaps between columns when using reverse video
        header_parts = []
        col = 0

        # Column 0: nsamples
        text = f"{'▼nsamples' if sort_col == 0 else 'nsamples':>13}  "
        header_parts.append((col, text, sorted_header if sort_col == 0 else normal_header))
        col += 15

        # Column 1: sample %
        if show_sample_pct:
            text = f"{'▼%' if sort_col == 1 else '%':>5}  "
            header_parts.append((col, text, sorted_header if sort_col == 1 else normal_header))
            col += 7

        # Column 2: tottime
        if show_tottime:
            text = f"{'▼tottime' if sort_col == 2 else 'tottime':>10}  "
            header_parts.append((col, text, sorted_header if sort_col == 2 else normal_header))
            col += 12

        # Column 3: cumul %
        if show_cumul_pct:
            text = f"{'▼%' if sort_col == 3 else '%':>5}  "
            header_parts.append((col, text, sorted_header if sort_col == 3 else normal_header))
            col += 7

        # Column 4: cumtime
        if show_cumtime:
            text = f"{'▼cumtime' if sort_col == 4 else 'cumtime':>10}  "
            header_parts.append((col, text, sorted_header if sort_col == 4 else normal_header))
            col += 12

        # Remaining headers
        if col < width - 15:
            remaining_space = width - col - 1
            func_width = min(
                MAX_FUNC_NAME_WIDTH,
                max(MIN_FUNC_NAME_WIDTH, remaining_space // 2),
            )
            text = f"{'function':<{func_width}}  "
            header_parts.append((col, text, normal_header))
            col += func_width + 2

            if col < width - 10:
                file_text = "file:line"
                padding = width - col - len(file_text)
                text = file_text + " " * max(0, padding)
                header_parts.append((col, text, normal_header))

        # Draw full-width background first
        self.add_str(line, 0, " " * (width - 1), normal_header)

        # Draw each header part on top
        for col_pos, text, attr in header_parts:
            self.add_str(line, col_pos, text.rstrip(), attr)

        return (
            line + 1,
            show_sample_pct,
            show_tottime,
            show_cumul_pct,
            show_cumtime,
        )