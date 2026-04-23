def render(self, line, width, **kwargs):
        """Render opcode statistics panel.

        Args:
            line: Starting line number
            width: Available width
            kwargs: Must contain 'stats_list', 'height'

        Returns:
            Next available line number
        """
        stats_list = kwargs.get("stats_list", [])
        height = kwargs.get("height", 24)
        selected_row = self.collector.selected_row
        scroll_offset = getattr(self.collector, 'scroll_offset', 0)

        A_BOLD = self.display.get_attr("A_BOLD")
        A_NORMAL = self.display.get_attr("A_NORMAL")
        color_cyan = self.colors.get("color_cyan", A_NORMAL)
        color_yellow = self.colors.get("color_yellow", A_NORMAL)
        color_magenta = self.colors.get("color_magenta", A_NORMAL)

        # Get the selected function from stats_list (accounting for scroll)
        actual_index = scroll_offset + selected_row
        if not stats_list or actual_index >= len(stats_list):
            self.add_str(line, 0, "No function selected (use j/k to select)", A_NORMAL)
            return line + 1

        selected_stat = stats_list[actual_index]
        func = selected_stat["func"]
        filename, lineno, funcname = func

        # Get opcode stats for this function
        opcode_stats = self.collector.opcode_stats.get(func, {})

        if not opcode_stats:
            self.add_str(line, 0, f"No opcode data for {funcname}() (requires --opcodes)", A_NORMAL)
            return line + 1

        # Sort opcodes by count
        sorted_opcodes = sorted(opcode_stats.items(), key=lambda x: -x[1])
        total_opcode_samples = sum(opcode_stats.values())

        # Draw header
        header = f"─── Opcodes for {funcname}() "
        header += "─" * max(0, width - len(header) - 1)
        self.add_str(line, 0, header[:width-1], color_cyan | A_BOLD)
        line += 1

        # Calculate max samples for bar scaling
        max_count = sorted_opcodes[0][1] if sorted_opcodes else 1

        # Draw opcode rows (limit to available space)
        max_rows = min(8, height - line - 3)  # Leave room for footer
        bar_width = 20

        for i, (opcode_num, count) in enumerate(sorted_opcodes[:max_rows]):
            if line >= height - 3:
                break

            opcode_info = get_opcode_info(opcode_num)
            is_specialized = opcode_info["is_specialized"]
            name_display = format_opcode(opcode_num)

            pct = (count / total_opcode_samples * 100) if total_opcode_samples > 0 else 0

            # Draw bar
            bar_fill = int((count / max_count) * bar_width) if max_count > 0 else 0
            bar = "█" * bar_fill + "░" * (bar_width - bar_fill)

            # Format: [████████░░░░] LOAD_ATTR  45.2% (1234)
            # Specialized opcodes shown in magenta, base opcodes in yellow
            name_color = color_magenta if is_specialized else color_yellow

            row_text = f"[{bar}] {name_display:<35} {pct:>5.1f}% ({count:>6})"
            self.add_str(line, 2, row_text[:width-3], name_color)
            line += 1

        # Show "..." if more opcodes exist
        if len(sorted_opcodes) > max_rows:
            remaining = len(sorted_opcodes) - max_rows
            self.add_str(line, 2, f"... and {remaining} more opcodes", A_NORMAL)
            line += 1

        return line