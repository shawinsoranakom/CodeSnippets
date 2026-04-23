def render(self, line, width, **kwargs):
        """
        Render the footer at the specified position.

        Args:
            line: Starting line number (should be height - 2)
            width: Available width

        Returns:
            Next available line number
        """
        A_DIM = self.display.get_attr("A_DIM")
        A_BOLD = self.display.get_attr("A_BOLD")

        # Legend line
        legend = "nsamples: direct/cumulative (direct=executing, cumulative=on stack)"
        self.add_str(line, 0, legend[: width - 1], A_DIM)
        line += 1

        # Controls line with status
        sort_names = {
            "tottime": "Total Time",
            "nsamples": "Direct Samples",
            "cumtime": "Cumulative Time",
            "sample_pct": "Sample %",
            "cumul_pct": "Cumulative %",
        }
        sort_display = sort_names.get(
            self.collector.sort_by, self.collector.sort_by
        )

        # Build status indicators
        status = []
        if self.collector.finished:
            status.append("[PROFILING FINISHED - Press 'q' to quit]")
        elif self.collector.paused:
            status.append("[PAUSED]")
        if self.collector.filter_pattern:
            status.append(
                f"[Filter: {self.collector.filter_pattern} (c to clear)]"
            )
        # Show trend colors status if disabled
        if self.collector._trend_tracker is not None and not self.collector._trend_tracker.enabled:
            status.append("[Trend colors: OFF]")
        status_str = " ".join(status) + " " if status else ""

        if self.collector.finished:
            footer = f"{status_str}"
        else:
            footer = f"{status_str}Sort: {sort_display} | 't':mode 'x':trends ←→:thread 'h':help 'q':quit"
        self.add_str(
            line,
            0,
            footer[: width - 1],
            A_BOLD
            if (self.collector.paused or self.collector.finished)
            else A_DIM,
        )

        return line + 1