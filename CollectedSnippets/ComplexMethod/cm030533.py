def draw_top_functions(self, line, width, stats_list):
        """Draw top N hottest functions."""
        col = 0
        self.add_str(
            line,
            col,
            f"Top {TOP_FUNCTIONS_DISPLAY_COUNT}:     ",
            curses.A_BOLD,
        )
        col += 11

        top_by_samples = sorted(
            stats_list, key=lambda x: x["direct_calls"], reverse=True
        )
        emojis = ["🥇", "🥈", "🥉"]
        medal_colors = [
            self.colors["red"],
            self.colors["yellow"],
            self.colors["green"],
        ]

        displayed = 0
        for func_data in top_by_samples:
            if displayed >= TOP_FUNCTIONS_DISPLAY_COUNT:
                break
            if col >= width - 20:
                break
            if func_data["direct_calls"] == 0:
                continue

            func_name = func_data["func"][2]
            func_pct = func_data["sample_pct"]

            # Medal emoji
            if col + 3 < width - 15:
                self.add_str(
                    line, col, emojis[displayed] + " ", medal_colors[displayed]
                )
                col += 3

            # Function name (truncate to fit)
            available_for_name = width - col - 15
            max_name_len = min(25, max(5, available_for_name))
            if len(func_name) > max_name_len:
                func_name = func_name[: max_name_len - 3] + "..."

            if col + len(func_name) < width - 10:
                self.add_str(line, col, func_name, medal_colors[displayed])
                col += len(func_name)

                pct_str = (
                    f" ({func_pct:.1f}%)"
                    if func_pct >= 0.1
                    else f" ({func_data['direct_calls']})"
                )
                self.add_str(line, col, pct_str, curses.A_DIM)
                col += len(pct_str)

                displayed += 1

                if displayed < 3 and col < width - 30:
                    self.add_str(line, col, " │ ", curses.A_DIM)
                    col += 3

        if displayed == 0 and col < width - 25:
            self.add_str(line, col, "(collecting samples...)", curses.A_DIM)

        return line + 1