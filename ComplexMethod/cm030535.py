def draw_stats_rows(self, line, height, width, stats_list, column_flags):
        """Draw the statistics data rows."""
        show_sample_pct, show_tottime, show_cumul_pct, show_cumtime = (
            column_flags
        )

        # Get color attributes
        color_file = self.colors.get("color_file", curses.A_NORMAL)
        color_func = self.colors.get("color_func", curses.A_NORMAL)

        # Get trend tracker for color decisions
        trend_tracker = self.collector._trend_tracker

        # Check if opcode mode is enabled for row selection highlighting
        show_opcodes = getattr(self.collector, 'show_opcodes', False)
        selected_row = getattr(self.collector, 'selected_row', 0)
        scroll_offset = getattr(self.collector, 'scroll_offset', 0) if show_opcodes else 0
        A_REVERSE = self.display.get_attr("A_REVERSE")
        A_BOLD = self.display.get_attr("A_BOLD")

        # Reserve space for opcode panel when enabled
        opcode_panel_height = OPCODE_PANEL_HEIGHT if show_opcodes else 0

        # Apply scroll offset when in opcode mode
        display_stats = stats_list[scroll_offset:] if show_opcodes else stats_list

        for row_idx, stat in enumerate(display_stats):
            if line >= height - FOOTER_LINES - opcode_panel_height:
                break

            func = stat["func"]
            direct_calls = stat["direct_calls"]
            cumulative_calls = stat["cumulative_calls"]
            total_time = stat["total_time"]
            cumulative_time = stat["cumulative_time"]
            sample_pct = stat["sample_pct"]
            cum_pct = stat["cumul_pct"]
            trends = stat.get("trends", {})

            # Check if this row is selected
            is_selected = show_opcodes and row_idx == selected_row

            # Helper function to get trend color
            def get_trend_color(column_name):
                if is_selected:
                    return A_REVERSE | A_BOLD
                trend = trends.get(column_name, "stable")
                if trend_tracker is not None and trend_tracker.enabled:
                    return trend_tracker.get_color(trend)
                return curses.A_NORMAL

            filename, lineno, funcname = func[0], func[1], func[2]
            samples_str = f"{direct_calls}/{cumulative_calls}"
            col = 0

            # Fill entire row with reverse video background for selected row
            if is_selected:
                self.add_str(line, 0, " " * (width - 1), A_REVERSE | A_BOLD)

            # Show selection indicator when opcode panel is enabled
            if show_opcodes:
                if is_selected:
                    self.add_str(line, col, "►", A_REVERSE | A_BOLD)
                else:
                    self.add_str(line, col, " ", curses.A_NORMAL)
                col += 2

            # Samples column - apply trend color based on nsamples trend
            nsamples_color = get_trend_color("nsamples")
            self.add_str(line, col, f"{samples_str:>13}  ", nsamples_color)
            col += 15

            # Sample % column
            if show_sample_pct:
                sample_pct_color = get_trend_color("sample_pct")
                self.add_str(line, col, f"{sample_pct:>5.1f}  ", sample_pct_color)
                col += 7

            # Total time column
            if show_tottime:
                tottime_color = get_trend_color("tottime")
                self.add_str(line, col, f"{total_time:>10.3f}  ", tottime_color)
                col += 12

            # Cumul % column
            if show_cumul_pct:
                cumul_pct_color = get_trend_color("cumul_pct")
                self.add_str(line, col, f"{cum_pct:>5.1f}  ", cumul_pct_color)
                col += 7

            # Cumul time column
            if show_cumtime:
                cumtime_color = get_trend_color("cumtime")
                self.add_str(line, col, f"{cumulative_time:>10.3f}  ", cumtime_color)
                col += 12

            # Function name column
            if col < width - 15:
                remaining_space = width - col - 1
                func_width = min(
                    MAX_FUNC_NAME_WIDTH,
                    max(MIN_FUNC_NAME_WIDTH, remaining_space // 2),
                )

                func_display = funcname
                if len(funcname) > func_width:
                    func_display = funcname[: func_width - 3] + "..."
                func_display = f"{func_display:<{func_width}}"
                func_color = A_REVERSE | A_BOLD if is_selected else color_func
                self.add_str(line, col, func_display, func_color)
                col += func_width + 2

                # File:line column
                if col < width - 10:
                    simplified_path = self.collector.simplify_path(filename)
                    file_line = f"{simplified_path}:{lineno}"
                    remaining_width = width - col - 1
                    file_color = A_REVERSE | A_BOLD if is_selected else color_file
                    self.add_str(
                        line, col, file_line[:remaining_width], file_color
                    )

            line += 1

        return line